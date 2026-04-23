# AI Video Generation Platform

A cloud-based AI video generation platform with a conversational chat interface. Users type natural language prompts, the AI enhances them automatically using LLMs, generates cinematic videos via cloud ML models, and delivers them with streaming progress updates.

> **Think ChatGPT meets Runway** -- a Grok-style assistant purpose-built for video creation.

---

## Architecture

```
+------------------------------------------------------------------+
|                        CLIENT (Android)                           |
|  +-------------+  +-------------+  +-------------+               |
|  |  Chat UI    |  |   Video     |  |  Gallery    |               |
|  |             |  |   Player    |  |             |               |
|  +------+------+  +------+------+  +------+------+               |
|         |                |                |                       |
|  +------v----------------v----------------v------+               |
|  |           ViewModel Layer                    |               |
|  |  ChatViewModel | VideoViewModel | GalleryVM   |               |
|  +------+--------------------------------+------+               |
|         |                                |                       |
|  +------v--------------------------------v------+               |
|  |         Repository Layer                      |               |
|  |  ChatRepository | VideoRepository | Presets   |               |
|  +------+--------------------------------+------+               |
|         |                                |                       |
|  +------v--------------------------------v------+               |
|  |         API Client (Retrofit/OkHttp/SSE)     |               |
|  +----------------------+-----------------------+               |
+-------------------------|----------------------------------------+
                          | HTTPS / SSE
+-------------------------v----------------------------------------+
|                      CLOUD BACKEND                                |
|  +-----------------------------------------------------------+   |
|  |              API Gateway (FastAPI)                         |   |
|  |  /api/v1/chat  /api/v1/generate  /api/v1/videos          |   |
|  +----------------------+------------------------------------+   |
|                         |                                       |
|  +----------------------v------------------------------------+   |
|  |           Service Layer                                    |   |
|  |  ChatService | VideoService | PromptService               |   |
|  +----------------------+------------------------------------+   |
|                         |                                       |
|  +----------------------v------------------------------------+   |
|  |          External API Integrations                         |   |
|  |  LLM API (OpenAI/Claude) -> prompt enhancement            |   |
|  |  Video Gen API (Runway/Kling) -> video generation         |   |
|  |  Cloud Storage (S3/R2) -> video hosting                   |   |
|  +-----------------------------------------------------------+   |
|                                                                  |
|  +-----------------------------------------------------------+   |
|  |          Data Layer                                        |   |
|  |  PostgreSQL (videos, chat history)                        |   |
|  |  Redis (cache, job queue, SSE pub/sub)                    |   |
|  |  Celery Workers (background generation)                   |   |
|  +-----------------------------------------------------------+   |
+------------------------------------------------------------------+
```

---

## Tech Stack

### Frontend (Android)
| Component | Technology |
|-----------|-----------|
| Language | Kotlin 2.0 |
| UI Framework | Jetpack Compose |
| Architecture | MVVM + Repository Pattern |
| Dependency Injection | Hilt |
| Networking | Retrofit + OkHttp |
| Streaming | SSE (Server-Sent Events) |
| Video Playback | ExoPlayer |
| Image Loading | Coil |
| Async | Coroutines + Flow |

### Backend (Cloud)
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Background Jobs | Celery |
| LLM Integration | OpenAI/Claude API |
| Video Generation | RunwayML / Kling / Fal.ai |
| Storage | AWS S3 / Cloudflare R2 |
| Deployment | Docker + Docker Compose |

---

## Project Structure

```
aivideo/
+-- design/
|   +-- design.md              # Full design spec (tokens, screens, animations)
|
+-- backend/
|   +-- main.py                # FastAPI app with all endpoints
|   +-- tasks.py               # Celery background tasks
|   +-- requirements.txt       # Python dependencies
|   +-- Dockerfile             # Backend container image
|   +-- docker-compose.yml     # Full stack orchestration
|   +-- .env.example           # Environment template
|
+-- android/
|   +-- app/
|   |   +-- src/main/java/com/aivideo/
|   |   |   +-- MainActivity.kt           # Entry point with navigation
|   |   |   +-- AiVideoApp.kt             # Hilt Application class
|   |   |   |
|   |   |   +-- data/
|   |   |   |   +-- model/
|   |   |   |   |   +-- Models.kt         # All data classes
|   |   |   |   +-- remote/
|   |   |   |   |   +-- ApiService.kt     # Retrofit API interface
|   |   |   |   |   +-- RetrofitClient.kt # HTTP client config
|   |   |   |   |   +-- SseClient.kt      # SSE streaming client
|   |   |   |   +-- repository/
|   |   |   |       +-- ChatRepository.kt
|   |   |   |       +-- VideoRepository.kt
|   |   |   |       +-- PresetRepository.kt
|   |   |   |
|   |   |   +-- viewmodel/
|   |   |   |   +-- ChatViewModel.kt      # Chat UI state management
|   |   |   |   +-- GalleryViewModel.kt   # Gallery state management
|   |   |   |   +-- SettingsViewModel.kt  # Settings state management
|   |   |   |
|   |   |   +-- ui/
|   |   |   |   +-- theme/
|   |   |   |   |   +-- Theme.kt          # Colors, typography, shapes
|   |   |   |   +-- components/
|   |   |   |   |   +-- VideoPlayer.kt    # Video player composables
|   |   |   |   +-- chat/
|   |   |   |   |   +-- ChatScreen.kt     # Main chat interface
|   |   |   |   +-- gallery/
|   |   |   |   |   +-- GalleryScreen.kt  # Video gallery grid
|   |   |   |   +-- settings/
|   |   |   |       +-- SettingsScreen.kt # App settings
|   |   |   |
|   |   |   +-- di/
|   |   |       +-- AppModule.kt          # Hilt DI providers
|   |   |
|   |   +-- src/main/res/                 # Android resources
|   |   +-- build.gradle.kts              # App-level build config
|   |
|   +-- build.gradle.kts                  # Project-level build config
|
+-- README.md                             # This file
```

---

## Getting Started

### Prerequisites

- Android Studio Hedgehog (2023.1.1) or later
- Python 3.11+
- Docker & Docker Compose (for backend)
- OpenAI API key (for prompt enhancement)
- Video generation API key (RunwayML / Kling / Fal.ai)

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create environment file
cp .env.example .env
# Edit .env with your API keys

# 3. Start with Docker Compose
docker-compose up -d

# Or run locally:
# python -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Android Setup

```bash
# 1. Open android/ folder in Android Studio
# 2. Sync project with Gradle files
# 3. Update API_BASE_URL in app/build.gradle.kts if needed
# 4. Run on emulator or device
```

### Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://aivideo:aivideo@localhost:5432/aivideo` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `LLM_API_KEY` | OpenAI/Claude API key | Required |
| `LLM_API_URL` | LLM API endpoint | `https://api.openai.com/v1/chat/completions` |
| `VIDEO_API_KEY` | Video generation API key | Required |
| `VIDEO_API_URL` | Video API endpoint | `https://api.runwayml.com/v1` |
| `STORAGE_URL` | CDN/storage base URL | Required |

---

## API Endpoints

### Chat & Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat` | Start generation, return video ID |
| `GET` | `/api/v1/chat/{id}/stream` | SSE stream for progress |
| `POST` | `/api/v1/generate` | Non-streaming generation |
| `POST` | `/api/v1/enhance-prompt` | Prompt enhancement only |
| `GET` | `/api/v1/chat/history` | Chat message history |

### Videos
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/videos` | List all videos |
| `GET` | `/api/v1/videos/{id}` | Get video details |
| `DELETE` | `/api/v1/videos/{id}` | Delete video |
| `GET` | `/api/v1/videos/{id}/download` | Get download URL |

### Presets
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/presets` | List prompt presets |
| `GET` | `/api/v1/presets/categories` | List preset categories |

---

## SSE Event Types

The streaming endpoint sends these event types:

| Event | Data | Description |
|-------|------|-------------|
| `prompt_enhanced` | `{refined_prompt}` | AI-enhanced prompt |
| `status` | `{status, progress, message}` | Generation progress |
| `complete` | `{video: {...}}` | Generation finished |
| `error` | `{message}` | Error occurred |

---

## Prompt Presets

### Cinematic
- **Epic** - Sweeping aerial views, dramatic lighting, film grain
- **Horror** - Dark scenes, flickering lights, foggy atmosphere
- **Film Noir** - High contrast B&W, venetian blind shadows, rain
- **Romance** - Golden hour, soft bokeh, warm palette

### Animation
- **3D Pixar** - Vibrant colors, expressive characters, soft lighting
- **Anime** - Cel-shaded, dynamic angles, cherry blossoms
- **Stop Motion** - Clay figures, miniature sets, warm lighting

### Commercial
- **Product Ad** - Studio lighting, reflective surfaces, premium feel
- **Food** - Macro close-up, steam, editorial quality
- **Fashion** - Runway lighting, slow motion fabric, luxury

### Social
- **Vlog** - Handheld feel, natural lighting, authentic
- **Reels** - Fast-paced, vertical, eye-catching transitions
- **Tutorial** - Clean angles, step-by-step, educational

---

## Features

### Core
- [x] Conversational chat interface
- [x] Text-to-video generation
- [x] AI prompt enhancement (LLM-powered)
- [x] Streaming progress updates (SSE)
- [x] Video preview with ExoPlayer
- [x] Download generated videos
- [x] Gallery with grid layout
- [x] Generation history

### Generation Controls
- [x] Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)
- [x] Resolution (720p, 1080p, 4K, 8K)
- [x] Duration (4-12 seconds)
- [x] Camera motion prompts (dolly, zoom, pan)
- [x] Style presets (cinematic, anime, realistic)

### UI/UX
- [x] Dark theme with purple accent
- [x] Smooth animations and transitions
- [x] Typing indicator
- [x] Progress bars with glow effects
- [x] Empty states
- [x] Error handling with retry
- [x] Pull-to-refresh (gallery)
- [x] Multi-select for batch delete

---

## Roadmap

### Phase 1 (MVP)
- [x] Chat interface with streaming
- [x] Basic video generation
- [x] Prompt enhancement
- [x] Video gallery

### Phase 2
- [ ] Image-to-video generation
- [ ] Video-to-video editing
- [ ] User accounts & authentication
- [ ] Cloud storage integration
- [ ] Push notifications

### Phase 3
- [ ] Multi-modal input (audio, image)
- [ ] Custom model fine-tuning
- [ ] Community prompt gallery
- [ ] Batch generation
- [ ] Advanced camera controls

---

## License

MIT License - see LICENSE file for details.

---

## Support

For issues or questions, please open a GitHub issue or contact support@aivideo.app.
