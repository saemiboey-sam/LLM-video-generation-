# AI Video Generation Platform - Design Document

## Overview

A cloud-based AI video generation platform with a conversational chat interface. Users type natural language prompts, the AI enhances them automatically, generates cinematic videos via cloud ML models, and delivers them with a streaming progress experience. Think ChatGPT meets Runway — a Grok-style assistant purpose-built for video creation.

---

## Design Tokens

### Colors

| Token | Value | Usage |
|-------|-------|-------|
| Background Primary | `#0A0A0F` | Main app background, dark void |
| Background Secondary | `#12121A` | Card surfaces, elevated panels |
| Background Tertiary | `#1A1A24` | Input fields, hover states |
| Accent Primary | `#7C3AED` | Primary CTA, send button, active states |
| Accent Secondary | `#A78BFA` | Highlights, badges, secondary accents |
| Accent Glow | `#8B5CF6` | Glow effects, progress indicators |
| Text Primary | `#F8FAFC` | Headings, primary content |
| Text Secondary | `#94A3B8` | Body text, descriptions |
| Text Muted | `#64748B` | Timestamps, metadata |
| Border Subtle | `#27272A` | Dividers, card borders |
| Success | `#10B981` | Completed states, download ready |
| Warning | `#F59E0B` | Processing, loading states |
| Error | `#EF4444` | Error messages, failures |

### Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Display | Inter | 800 | 32sp |
| Heading | Inter | 700 | 24sp |
| Subheading | Inter | 600 | 18sp |
| Body | Inter | 400 | 16sp |
| Caption | Inter | 500 | 12sp |
| Mono | JetBrains Mono | 400 | 14sp | Code, timestamps |

### Spacing

| Token | Value |
|-------|-------|
| xs | 4dp |
| sm | 8dp |
| md | 16dp |
| lg | 24dp |
| xl | 32dp |
| 2xl | 48dp |

### Border Radius

| Token | Value |
|-------|-------|
| sm | 8dp |
| md | 12dp |
| lg | 16dp |
| xl | 24dp |
| full | 9999dp |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Android)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Chat UI  │  │ Video    │  │ Gallery  │  │ Settings │   │
│  │          │  │ Player   │  │          │  │          │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│  ┌────▼──────────────▼──────────────▼──────────────▼─────┐  │
│  │              ViewModel Layer                          │  │
│  │  ChatViewModel │ VideoViewModel │ GalleryViewModel    │  │
│  └────┬──────────────────┬──────────────────┬────────────┘  │
│       │                  │                  │               │
│  ┌────▼──────────────────▼──────────────────▼─────┐         │
│  │         Repository Layer                        │         │
│  │  ChatRepository │ VideoRepository │ SettingsRepo │         │
│  └────┬──────────────────┬──────────────────┬─────┘         │
│       │                  │                  │                │
│  ┌────▼──────────────────▼──────────────────▼─────┐         │
│  │         API Client (Retrofit/OkHttp)            │         │
│  └──────────────────────┬─────────────────────────┘         │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTPS/WSS
┌─────────────────────────▼───────────────────────────────────┐
│                    CLOUD BACKEND                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              API Gateway (FastAPI)                   │    │
│  │  /api/v1/chat  /api/v1/generate  /api/v1/videos    │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │           Service Layer                             │    │
│  │  ChatService │ VideoService │ PromptService        │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │          External API Integrations                  │    │
│  │  LLM API (prompt enhancement)                       │    │
│  │  Video Gen API (Runway/Kling/Internal)              │    │
│  │  Storage (S3/Cloud Storage)                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          Data Layer                                 │    │
│  │  PostgreSQL │ Redis (cache/queue) │ Celery Workers   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Frontend (Android):**
- Kotlin 2.0
- Jetpack Compose (UI)
- Hilt (DI)
- Retrofit + OkHttp (Networking)
- ExoPlayer (Video playback)
- Coil (Image loading)
- Room (Local caching)
- Coroutines + Flow
- Material Design 3

**Backend (Cloud):**
- Python 3.11
- FastAPI (Web framework)
- SQLAlchemy + PostgreSQL (Database)
- Redis (Cache + Queue)
- Celery (Background workers)
- OpenAI/Claude API (LLM prompt enhancement)
- RunwayML / Kling / Fal.ai API (Video generation)
- AWS S3 / Cloudflare R2 (Video storage)
- WebSocket (Streaming progress)

---

## Features & Behaviors

### 1. Chat Interface

**Layout:**
- Full-screen chat with gradient background (`#0A0A0F` to `#12121A`)
- Messages stacked vertically with auto-scroll
- User messages right-aligned with purple accent bubble (`#7C3AED` bg)
- AI messages left-aligned with dark card surface (`#1A1A24` bg)
- Sticky input bar at bottom with text field + send button + attachment

**Message Types:**
- Text message (user query)
- Video generation card (AI response with video)
- Progress indicator (streaming status)
- Prompt refinement suggestion card
- Error message card

**Animations:**
- Message entry: slide up 24dp + fade in, 300ms, ease-out
- Typing indicator: pulsing dots, 1.5s loop
- Send button: scale 0.9→1.0 on tap
- Video card reveal: fade in + scale 0.95→1.0, 400ms

### 2. Video Generation Flow

**User Journey:**
1. User types prompt (e.g., "a cat walking through Tokyo at night")
2. AI refines prompt automatically (shows "Enhancing your prompt...")
3. AI displays refined prompt in expandable card
4. Generation starts — progress bar appears
5. Streaming updates: "Queued" → "Generating frames..." → "Rendering video..." → "Complete"
6. Video card appears with player + download button

**Progress States:**
| State | Icon | Color | Message |
|-------|------|-------|---------|
| queued | clock | `#64748B` | "In queue..." |
| enhancing | sparkle | `#A78BFA` | "Enhancing prompt..." |
| generating | loader | `#F59E0B` | "Generating frames..." |
| rendering | film | `#F59E0B` | "Rendering video..." |
| complete | check | `#10B981` | "Ready!" |
| error | alert | `#EF4444` | "Generation failed" |

### 3. Prompt Refinement System

**LLM Enhancement Prompt:**
```
You are a professional video prompt engineer. Enhance the user's prompt for AI video generation.
Add cinematic details: lighting, camera movement, atmosphere, style.
Keep the core intent. Return ONLY the enhanced prompt, no commentary.

Original: "a cat walking through Tokyo"
Enhanced: "A majestic fluffy cat walking through neon-lit Tokyo streets at night, 
rain-slicked pavement reflecting colorful signs, cinematic depth of field, 
slow dolly camera following from behind, atmospheric fog, cyberpunk aesthetic, 
4K quality, photorealistic"
```

**UI Display:**
- Collapsible card showing "Original → Enhanced"
- Diff highlighting (added words in purple)
- "Use original" toggle option

### 4. Prompt Presets

**Categories:**
| Category | Icon | Presets |
|----------|------|---------|
| Cinematic | film | Epic, Horror, Romance, Noir |
| Animation | palette | 3D Pixar, Anime, Stop Motion |
| Commercial | trending | Product Ad, Food, Fashion |
| Social | share | Vlog, Reels, Tutorial |

**Preset Card UI:**
- Horizontal scrollable chips
- Each chip: icon + label, tap to apply template
- Active state: filled purple background

### 5. Video Player

**Controls:**
- Play/Pause center button (circular, 64dp)
- Progress bar with draggable scrubber
- Timestamp display (current/total)
- Fullscreen toggle
- Loop toggle
- Download button (top-right)

**Gestures:**
- Tap center: play/pause
- Double tap left/right: seek -10s/+10s
- Pinch: fullscreen toggle
- Long press: 2x speed

### 6. Gallery Screen

**Layout:**
- Staggered grid (2 columns)
- Video thumbnails with duration badge
- Tap to open detail view
- Long press for multi-select (delete/share)
- Pull-to-refresh

**Thumbnail Card:**
- Aspect ratio maintained from generation
- Gradient overlay at bottom with title
- Three-dot menu: download, share, delete

### 7. Settings Screen

**Options:**
- Account (API key / subscription)
- Generation defaults (aspect ratio, resolution, duration)
- Prompt enhancement toggle
- Auto-download toggle
- Theme (Dark always)
- About / Help

---

## Data Models

### ChatMessage
```kotlin
data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val role: MessageRole, // USER, ASSISTANT, SYSTEM
    val content: String,
    val type: MessageType, // TEXT, VIDEO, PROGRESS, ERROR
    val videoUrl: String? = null,
    val videoMetadata: VideoMetadata? = null,
    val refinedPrompt: String? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val status: GenerationStatus? = null
)
```

### VideoMetadata
```kotlin
data class VideoMetadata(
    val id: String,
    val prompt: String,
    val refinedPrompt: String?,
    val duration: Int, // seconds
    val resolution: String, // "720p", "1080p", "4K"
    val aspectRatio: AspectRatio, // SQUARE, WIDE, PORTRAIT
    val style: String?, // cinematic, anime, etc.
    val url: String,
    val thumbnailUrl: String?,
    val createdAt: Long,
    val fileSize: Long?
)
```

### GenerationRequest
```kotlin
data class GenerationRequest(
    val prompt: String,
    val enhancePrompt: Boolean = true,
    val aspectRatio: AspectRatio = AspectRatio.WIDE,
    val resolution: Resolution = Resolution.HD,
    val duration: Int = 5, // 4-12 seconds
    val style: String? = null,
    val cameraMotion: String? = null // dolly, zoom, pan
)
```

### PromptPreset
```kotlin
data class PromptPreset(
    val id: String,
    val name: String,
    val category: PresetCategory,
    val icon: String,
    val template: String
)
```

---

## API Specification

### Base URL: `/api/v1`

#### POST `/chat`
Send a message and start generation.
```json
// Request
{
  "prompt": "a cat walking through Tokyo",
  "enhance_prompt": true,
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "duration": 5,
  "style": "cinematic"
}

// Response (streaming via SSE)
{"type": "prompt_enhanced", "refined_prompt": "..."}
{"type": "status", "status": "queued", "position": 3}
{"type": "status", "status": "generating", "progress": 15}
{"type": "status", "status": "rendering", "progress": 75}
{"type": "complete", "video": {"id": "...", "url": "...", "metadata": {...}}}
```

#### GET `/videos`
List user's generated videos.
```json
// Response
{
  "videos": [
    {"id": "...", "prompt": "...", "url": "...", "thumbnail_url": "...", "created_at": "..."}
  ]
}
```

#### GET `/videos/{id}`
Get single video details.

#### DELETE `/videos/{id}`
Delete a video.

#### POST `/videos/{id}/download`
Generate download URL.

#### GET `/presets`
Get all prompt presets.

#### POST `/enhance-prompt`
Enhance a prompt via LLM.

---

## Animations & Interactions

### Message Entry
- Slide up from 24dp below + fade in
- Duration: 300ms
- Easing: `FastOutSlowInEasing`
- Stagger: 50ms between messages

### Typing Indicator
- Three dots pulsing sequentially
- Scale 0.5→1.0→0.5
- Duration: 1.5s loop
- Color: `#7C3AED`

### Progress Bar
- Continuous indeterminate animation while generating
- Segmented progress for known steps
- Glow effect on the leading edge (`#8B5CF6` shadow)

### Video Card Reveal
- Scale: 0.95→1.0
- Opacity: 0→1
- Duration: 400ms
- Easing: `Spring(dampingRatio = 0.8, stiffness = 300)`

### Button Press
- Scale: 1.0→0.95 on press
- Background color darken 10%
- Duration: 100ms

### Screen Transitions
- Slide horizontal between screens
- Duration: 300ms
- Fade overlap: 100ms

---

## Prompt Templates (Presets)

### Cinematic
```
Epic: "Epic cinematic shot, sweeping aerial view, dramatic orchestral atmosphere, 
volumetric lighting, anamorphic lens flares, Hollywood production quality, 35mm film grain"

Horror: "Dark horror scene, flickering candlelight, long shadows, foggy atmosphere, 
unsettling tension, found footage style, desaturated color palette, jump scare framing"

Noir: "Film noir style, high contrast black and white, venetian blind shadows, 
rainy city street, detective silhouette, dramatic side lighting, 1940s aesthetic"
```

### Animation
```
3D Pixar: "3D Pixar-style animation, vibrant colors, expressive characters, 
soft diffused lighting, detailed textures, family-friendly, cinematic composition"

Anime: "Japanese anime style, cel-shaded, dynamic camera angles, 
speed lines, cherry blossom atmosphere, Studio Ghibli inspired, hand-painted backgrounds"

Stop Motion: "Stop motion animation, handcrafted clay figures, 
visible fingerprints texture, slightly jerky movement, miniature sets, warm lighting"
```

---

## Responsive Considerations

- **Phone (<600dp):** Full-width chat, single column gallery
- **Tablet (600-900dp):** Side panel for gallery, larger video player
- **Landscape:** Video player expands to full width, chat collapses to drawer

---

## Performance

- Video thumbnails: lazy loading with Coil
- Chat messages: RecyclerView/Compose LazyColumn with viewport caching
- API calls: Retrofit with connection pooling
- Downloads: OkHttp streaming with progress callback
- Cache: Room DB for offline message history

---

## Security

- API keys stored in `local.properties` (never committed)
- Token-based auth (JWT) stored in EncryptedSharedPreferences
- HTTPS only for all API calls
- Certificate pinning for production
- Rate limiting on generation endpoints
