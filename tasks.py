"""
Celery background tasks for video generation
Handles long-running video generation jobs asynchronously
"""

import os
import uuid
from datetime import datetime

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from main import VideoRecord, LLMService, VideoGenerationService

# Celery app
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("aivideo", broker=REDIS_URL, backend=REDIS_URL)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aivideo:aivideo@localhost:5432/aivideo")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, max_retries=3)
def generate_video_task(self, video_id: str, prompt: str, **kwargs):
    """
    Background task for video generation.
    This runs the full generation pipeline asynchronously.
    """
    db = SessionLocal()
    llm = LLMService()
    
    try:
        # Get video record
        video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        # Step 1: Enhance prompt
        if kwargs.get("enhance_prompt", True):
            video.status = "enhancing"
            db.commit()
            
            refined = llm.enhance_prompt(prompt, kwargs.get("style"))
            video.refined_prompt = refined
            db.commit()
        
        # Step 2: Generate
        video.status = "generating"
        video.progress = 15
        db.commit()
        
        # In production: call actual video API
        # For now, simulate progress
        import time
        for progress in range(20, 100, 10):
            time.sleep(2)  # Simulate generation time
            video.progress = progress
            if progress < 70:
                video.status = "generating"
            else:
                video.status = "rendering"
            db.commit()
        
        # Step 3: Complete
        video.status = "complete"
        video.progress = 100
        video.url = f"https://storage.example.com/videos/{video_id}.mp4"
        video.thumbnail_url = f"https://storage.example.com/videos/{video_id}_thumb.jpg"
        db.commit()
        
        return {"status": "complete", "video_id": video_id, "url": video.url}
        
    except Exception as exc:
        video = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
        if video:
            video.status = "error"
            video.error_message = str(exc)
            db.commit()
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
    finally:
        db.close()

@celery_app.task
def cleanup_old_videos(days: int = 30):
    """Delete videos older than specified days"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)
        old_videos = db.query(VideoRecord).filter(VideoRecord.created_at < cutoff).all()
        
        for video in old_videos:
            # Delete from storage
            # delete_from_storage(video.url)
            db.delete(video)
        
        db.commit()
        return {"deleted": len(old_videos)}
    finally:
        db.close()

@celery_app.task
def generate_thumbnail(video_id: str):
    """Generate thumbnail for a video"""
    # Implementation would use ffmpeg or similar
    pass
