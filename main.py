"""
AI Video Generation Platform - FastAPI Backend
Cloud-based video generation with LLM prompt enhancement
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import httpx
import redis.asyncio as redis
from contextlib import asynccontextmanager

# ─── Configuration ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aivideo:aivideo@localhost:5432/aivideo")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-your-key")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
VIDEO_API_KEY = os.getenv("VIDEO_API_KEY", "your-video-api-key")
VIDEO_API_URL = os.getenv("VIDEO_API_URL", "https://api.runwayml.com/v1")
STORAGE_URL = os.getenv("STORAGE_URL", "https://storage.yourcdn.com")

# ─── Database Setup ─────────────────────────────────────────────────────────
Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class VideoRecord(Base):
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="anonymous")
    prompt = Column(Text, nullable=False)
    refined_prompt = Column(Text, nullable=True)
    status = Column(String, default="queued")  # queued, generating, rendering, complete, error
    progress = Column(Integer, default=0)
    url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    duration = Column(Integer, default=5)
    resolution = Column(String, default="1080p")
    aspect_ratio = Column(String, default="16:9")
    style = Column(String, nullable=True)
    camera_motion = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessageRecord(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="anonymous")
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # text, video, progress, error
    video_id = Column(String, nullable=True)
    refined_prompt = Column(Text, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Redis Setup ────────────────────────────────────────────────────────────
redis_client: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

# ─── Pydantic Models ────────────────────────────────────────────────────────

class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    enhance_prompt: bool = True
    aspect_ratio: str = "16:9"
    resolution: str = "1080p"
    duration: int = Field(default=5, ge=4, le=12)
    style: Optional[str] = None
    camera_motion: Optional[str] = None

class GenerationResponse(BaseModel):
    id: str
    status: str
    message: str

class VideoResponse(BaseModel):
    id: str
    prompt: str
    refined_prompt: Optional[str]
    status: str
    progress: int
    url: Optional[str]
    thumbnail_url: Optional[str]
    duration: int
    resolution: str
    aspect_ratio: str
    style: Optional[str]
    file_size: Optional[int]
    created_at: datetime

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    message_type: str
    video_id: Optional[str]
    refined_prompt: Optional[str]
    status: Optional[str]
    created_at: datetime

class PromptEnhanceRequest(BaseModel):
    prompt: str
    style: Optional[str] = None

class PromptEnhanceResponse(BaseModel):
    original: str
    enhanced: str

class PromptPresetModel(BaseModel):
    id: str
    name: str
    category: str
    icon: str
    template: str

# ─── Prompt Presets Data ────────────────────────────────────────────────────

PROMPT_PRESETS = [
    # Cinematic
    {"id": "epic", "name": "Epic", "category": "cinematic", "icon": "film",
     "template": "Epic cinematic shot, sweeping aerial view, dramatic orchestral atmosphere, volumetric lighting, anamorphic lens flares, Hollywood production quality, 35mm film grain"},
    {"id": "horror", "name": "Horror", "category": "cinematic", "icon": "ghost",
     "template": "Dark horror scene, flickering candlelight, long shadows, foggy atmosphere, unsettling tension, found footage style, desaturated color palette, jump scare framing"},
    {"id": "noir", "name": "Film Noir", "category": "cinematic", "icon": "moon",
     "template": "Film noir style, high contrast black and white, venetian blind shadows, rainy city street, detective silhouette, dramatic side lighting, 1940s aesthetic"},
    {"id": "romance", "name": "Romance", "category": "cinematic", "icon": "heart",
     "template": "Romantic cinematic scene, golden hour lighting, soft focus bokeh, warm color palette, intimate atmosphere, slow motion feel, emotional depth"},
    # Animation
    {"id": "pixar", "name": "3D Pixar", "category": "animation", "icon": "box",
     "template": "3D Pixar-style animation, vibrant colors, expressive characters, soft diffused lighting, detailed textures, family-friendly, cinematic composition"},
    {"id": "anime", "name": "Anime", "category": "animation", "icon": "wind",
     "template": "Japanese anime style, cel-shaded, dynamic camera angles, speed lines, cherry blossom atmosphere, Studio Ghibli inspired, hand-painted backgrounds"},
    {"id": "stopmotion", "name": "Stop Motion", "category": "animation", "icon": "hand",
     "template": "Stop motion animation, handcrafted clay figures, visible fingerprints texture, slightly jerky movement, miniature sets, warm lighting"},
    # Commercial
    {"id": "product", "name": "Product Ad", "category": "commercial", "icon": "shopping",
     "template": "Professional product advertisement, clean studio lighting, rotating product view, sleek reflective surface, premium feel, commercial photography style"},
    {"id": "food", "name": "Food", "category": "commercial", "icon": "coffee",
     "template": "Professional food cinematography, macro close-up, steam rising, perfect lighting, mouth-watering colors, slow motion, overhead angle, editorial quality"},
    {"id": "fashion", "name": "Fashion", "category": "commercial", "icon": "shirt",
     "template": "High fashion editorial, dramatic runway lighting, confident model walk, haute couture, slow motion fabric movement, luxury atmosphere"},
    # Social
    {"id": "vlog", "name": "Vlog", "category": "social", "icon": "video",
     "template": "Vlog style footage, handheld camera feel, natural lighting, authentic moment, dynamic transitions, energetic pace, social media native"},
    {"id": "reels", "name": "Reels", "category": "social", "icon": "smartphone",
     "template": "Vertical social media video, fast-paced editing, trending audio visual, text overlay style, eye-catching transitions, hook in first second"},
    {"id": "tutorial", "name": "Tutorial", "category": "social", "icon": "book",
     "template": "Clean tutorial video, top-down or side angle, clear lighting, step-by-step visual, screen recording style overlay, educational and engaging"},
]

# ─── Services ───────────────────────────────────────────────────────────────

class LLMService:
    """Service for LLM-based prompt enhancement"""
    
    SYSTEM_PROMPT = """You are a professional video prompt engineer specializing in AI video generation.
Enhance the user's prompt by adding cinematic details, camera movement, lighting, atmosphere, and style.
Keep the core subject and intent intact. Return ONLY the enhanced prompt text — no explanations, no quotes."""

    async def enhance_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        """Enhance a user prompt using LLM API"""
        try:
            style_hint = f" Apply a {style} visual style." if style else ""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    LLM_API_URL,
                    headers={
                        "Authorization": f"Bearer {LLM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": self.SYSTEM_PROMPT},
                            {"role": "user", "content": f"Enhance this video prompt:{style_hint}\n\n{prompt}"}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 300
                    }
                )
                response.raise_for_status()
                data = response.json()
                enhanced = data["choices"][0]["message"]["content"].strip()
                # Remove quotes if present
                enhanced = enhanced.strip('"').strip("'")
                return enhanced
        except Exception as e:
            # Fallback: apply basic template enhancement
            return self._fallback_enhance(prompt, style)
    
    def _fallback_enhance(self, prompt: str, style: Optional[str] = None) -> str:
        """Basic enhancement when LLM API fails"""
        enhancements = {
            "cinematic": "cinematic composition, dramatic lighting, film grain, professional color grading",
            "animation": "vibrant colors, smooth animation, detailed background, stylized aesthetic",
            "realistic": "photorealistic, hyper-detailed, natural lighting, 8K resolution, lifelike textures",
            "anime": "anime style, cel-shaded, expressive, vibrant colors, dynamic composition"
        }
        
        base = f"{prompt}, highly detailed, professional quality"
        if style and style.lower() in enhancements:
            base += f", {enhancements[style.lower()]}"
        else:
            base += ", cinematic lighting, high quality"
        return base

class VideoGenerationService:
    """Service for video generation via external API"""
    
    def __init__(self):
        self.llm = LLMService()
    
    async def generate_stream(
        self,
        request: GenerationRequest,
        video_id: str,
        db: Session
    ) -> AsyncGenerator[str, None]:
        """Generate video with streaming progress updates"""
        
        # Step 1: Enhance prompt
        if request.enhance_prompt:
            yield self._sse_event("status", {
                "status": "enhancing",
                "message": "Enhancing your prompt with AI...",
                "progress": 5
            })
            await asyncio.sleep(0.5)
            
            refined = await self.llm.enhance_prompt(request.prompt, request.style)
            
            # Update DB
            video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
            if video:
                video.refined_prompt = refined
                video.status = "enhancing"
                db.commit()
            
            yield self._sse_event("prompt_enhanced", {
                "original_prompt": request.prompt,
                "refined_prompt": refined
            })
            await asyncio.sleep(0.5)
        else:
            refined = request.prompt
        
        # Step 2: Queue
        yield self._sse_event("status", {
            "status": "queued",
            "message": "In queue for generation...",
            "progress": 10
        })
        await asyncio.sleep(1)
        
        # Step 3: Generate frames
        video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
        if video:
            video.status = "generating"
            db.commit()
        
        for progress in range(15, 75, 5):
            yield self._sse_event("status", {
                "status": "generating",
                "message": f"Generating video frames... ({progress}%)",
                "progress": progress
            })
            await asyncio.sleep(0.8)
        
        # Step 4: Render
        video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
        if video:
            video.status = "rendering"
            db.commit()
        
        for progress in range(75, 95, 5):
            yield self._sse_event("status", {
                "status": "rendering",
                "message": f"Rendering final video... ({progress}%)",
                "progress": progress
            })
            await asyncio.sleep(0.5)
        
        # Step 5: Call external video API (mock for now)
        video_url = await self._call_video_api(refined, request)
        
        # Step 6: Complete
        video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
        if video:
            video.status = "complete"
            video.progress = 100
            video.url = video_url
            video.thumbnail_url = f"{video_url}?thumb=1"
            db.commit()
        
        yield self._sse_event("complete", {
            "video": {
                "id": video_id,
                "url": video_url,
                "thumbnail_url": f"{video_url}?thumb=1",
                "prompt": request.prompt,
                "refined_prompt": refined,
                "duration": request.duration,
                "resolution": request.resolution,
                "aspect_ratio": request.aspect_ratio,
                "style": request.style
            }
        })
        
        yield self._sse_event("status", {
            "status": "complete",
            "message": "Video generation complete!",
            "progress": 100
        })
    
    async def _call_video_api(
        self,
        prompt: str,
        request: GenerationRequest
    ) -> str:
        """Call external video generation API"""
        try:
            # Map aspect ratio
            ratio_map = {"1:1": "1:1", "16:9": "16:9", "9:16": "9:16", "4:3": "4:3", "3:4": "3:4"}
            aspect = ratio_map.get(request.aspect_ratio, "16:9")
            
            # In production, call actual video API
            # async with httpx.AsyncClient(timeout=120.0) as client:
            #     response = await client.post(
            #         f"{VIDEO_API_URL}/generate",
            #         headers={"Authorization": f"Bearer {VIDEO_API_KEY}"},
            #         json={
            #             "prompt": prompt,
            #             "duration": request.duration,
            #             "aspect_ratio": aspect,
            #             "resolution": request.resolution
            #         }
            #     )
            #     data = response.json()
            #     return data["video_url"]
            
            # Mock response for demo
            await asyncio.sleep(2)
            mock_id = str(uuid.uuid4())[:8]
            return f"{STORAGE_URL}/videos/{mock_id}.mp4"
            
        except Exception as e:
            # Return mock URL on failure
            mock_id = str(uuid.uuid4())[:8]
            return f"{STORAGE_URL}/videos/{mock_id}.mp4"
    
    def _sse_event(self, event_type: str, data: dict) -> str:
        """Format SSE event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

# ─── FastAPI App ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    r = await get_redis()
    await r.set("server_start", datetime.utcnow().isoformat())
    yield
    # Shutdown
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="AI Video Generation Platform",
    description="Cloud-based AI video generation with LLM prompt enhancement",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
video_service = VideoGenerationService()

# ─── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ─── Chat & Generation ──────────────────────────────────────────────────────

@app.post("/api/v1/chat", response_model=GenerationResponse)
async def create_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a video generation and return the ID"""
    video_id = str(uuid.uuid4())
    
    # Create video record
    video = VideoRecord(
        id=video_id,
        prompt=request.prompt,
        status="queued",
        progress=0,
        duration=request.duration,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
        style=request.style,
        camera_motion=request.camera_motion
    )
    db.add(video)
    db.commit()
    
    # Store chat message
    chat_msg = ChatMessageRecord(
        role="user",
        content=request.prompt,
        message_type="text"
    )
    db.add(chat_msg)
    db.commit()
    
    return GenerationResponse(
        id=video_id,
        status="queued",
        message="Generation started. Connect to SSE stream for updates."
    )

@app.get("/api/v1/chat/{video_id}/stream")
async def stream_generation(
    video_id: str,
    request: GenerationRequest,
    db: Session = Depends(get_db)
):
    """SSE stream for generation progress"""
    
    async def event_stream():
        try:
            async for event in video_service.generate_stream(request, video_id, db):
                yield event
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/v1/generate")
async def generate_video(
    request: GenerationRequest,
    db: Session = Depends(get_db)
):
    """Non-streaming video generation"""
    video_id = str(uuid.uuid4())
    
    video = VideoRecord(
        id=video_id,
        prompt=request.prompt,
        status="queued",
        progress=0,
        duration=request.duration,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
        style=request.style
    )
    db.add(video)
    db.commit()
    
    # Enhance prompt
    refined = request.prompt
    if request.enhance_prompt:
        refined = await video_service.llm.enhance_prompt(request.prompt, request.style)
        video.refined_prompt = refined
        video.status = "generating"
        db.commit()
    
    # Generate video
    video_url = await video_service._call_video_api(refined, request)
    
    video.status = "complete"
    video.progress = 100
    video.url = video_url
    video.thumbnail_url = f"{video_url}?thumb=1"
    db.commit()
    
    return {
        "id": video_id,
        "status": "complete",
        "video": {
            "url": video_url,
            "prompt": request.prompt,
            "refined_prompt": refined,
            "duration": request.duration,
            "resolution": request.resolution,
            "aspect_ratio": request.aspect_ratio
        }
    }

# ─── Prompt Enhancement ─────────────────────────────────────────────────────

@app.post("/api/v1/enhance-prompt", response_model=PromptEnhanceResponse)
async def enhance_prompt(
    request: PromptEnhanceRequest,
):
    """Enhance a prompt without generating video"""
    enhanced = await video_service.llm.enhance_prompt(request.prompt, request.style)
    return PromptEnhanceResponse(
        original=request.prompt,
        enhanced=enhanced
    )

# ─── Prompt Presets ─────────────────────────────────────────────────────────

@app.get("/api/v1/presets", response_model=List[PromptPresetModel])
async def get_presets(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get all prompt presets, optionally filtered by category"""
    presets = PROMPT_PRESETS
    if category:
        presets = [p for p in presets if p["category"] == category]
    return [PromptPresetModel(**p) for p in presets]

@app.get("/api/v1/presets/categories")
async def get_preset_categories():
    """Get available preset categories"""
    categories = {}
    for p in PROMPT_PRESETS:
        cat = p["category"]
        if cat not in categories:
            categories[cat] = {"name": cat.title(), "count": 0}
        categories[cat]["count"] += 1
    return list(categories.values())

# ─── Video Management ───────────────────────────────────────────────────────

@app.get("/api/v1/videos", response_model=List[VideoResponse])
async def list_videos(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all generated videos"""
    videos = db.query(VideoRecord).order_by(VideoRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [
        VideoResponse(
            id=v.id,
            prompt=v.prompt,
            refined_prompt=v.refined_prompt,
            status=v.status,
            progress=v.progress,
            url=v.url,
            thumbnail_url=v.thumbnail_url,
            duration=v.duration,
            resolution=v.resolution,
            aspect_ratio=v.aspect_ratio,
            style=v.style,
            file_size=v.file_size,
            created_at=v.created_at
        )
        for v in videos
    ]

@app.get("/api/v1/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get a single video by ID"""
    video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoResponse(
        id=video.id,
        prompt=video.prompt,
        refined_prompt=video.refined_prompt,
        status=video.status,
        progress=video.progress,
        url=video.url,
        thumbnail_url=video.thumbnail_url,
        duration=video.duration,
        resolution=video.resolution,
        aspect_ratio=video.aspect_ratio,
        style=video.style,
        file_size=video.file_size,
        created_at=video.created_at
    )

@app.delete("/api/v1/videos/{video_id}")
async def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Delete a video"""
    video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
    return {"message": "Video deleted"}

@app.get("/api/v1/videos/{video_id}/download")
async def download_video(video_id: str, db: Session = Depends(get_db)):
    """Get download URL for a video"""
    video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not video or not video.url:
        raise HTTPException(status_code=404, detail="Video not found or not ready")
    return {"download_url": video.url, "filename": f"aivideo_{video_id}.mp4"}

# ─── Chat History ───────────────────────────────────────────────────────────

@app.get("/api/v1/chat/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get chat message history"""
    messages = db.query(ChatMessageRecord).order_by(ChatMessageRecord.created_at.desc()).limit(limit).all()
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            video_id=m.video_id,
            refined_prompt=m.refined_prompt,
            status=m.status,
            created_at=m.created_at
        )
        for m in reversed(messages)
    ]

# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
