# Newsly

Turns your newsletter emails into audio summaries. Connects to Gmail, uses Grok to summarize the content, converts it to speech, and emails you the audio file. Optionally generates video with burned-in subtitles.

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run with Docker:

```bash
docker compose up --build
```

The API runs on `http://localhost:8000`.

### Environment Variables

**API Security:**
- `API_KEY` - Required API key for authenticating requests (set a strong random string)
- `RATE_LIMIT_PER_MINUTE` - Max requests per minute per IP (default: `60`)

**Google/Gmail:**
- `GOOGLE_AUTH_CLIENT_ID` / `GOOGLE_AUTH_CLIENT_SECRET` - OAuth credentials
- `GOOGLE_AUTH_REFRESH_TOKEN` - Run `scripts/generate_refresh_token.py` to get this
- `GMAIL_PUBSUB_TOPIC_NAME` - For Gmail push notifications

**AI:**
- `GROK_API_KEY` - Your X.AI API key
- `GROK_MODEL` - Model to use (defaults to latest)

**TTS (ElevenLabs):**
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key (required)
- `ELEVENLABS_VOICE_ID` - Voice ID to use (default: `JBFqnCBsd6RMkjVDRZzb`)
- `ELEVENLABS_MODEL_ID` - Model to use (default: `eleven_multilingual_v2`)
- `TTS_OUTPUT_FORMAT` - `mp3`, `wav`, etc.

**Video Generation (Optional):**
- `VIDEO_ENABLED` - Set to `true` to generate MP4 videos with subtitles (default: `false`)
- `VIDEO_OUTPUT_FORMAT` - Video format (default: `mp4`)
- `VIDEO_OUTPUT_FILE` - Output filename without extension (default: `output`)
- `VIDEO_BACKGROUND_COLOR` - Hex color for video background (default: `#1a1a2e`)
- `VIDEO_BACKGROUND_IMAGE` - Optional path to background image
- `VIDEO_WIDTH` / `VIDEO_HEIGHT` - Video dimensions (default: `1080x1080`)
- `SUBTITLE_FONT_SIZE` - Font size for subtitles (default: `48`)
- `SUBTITLE_FONT_COLOR` - Subtitle text color (default: `white`)
- `SUBTITLE_MAX_CHARS_PER_LINE` - Max characters per subtitle line (default: `60`)

When enabled, both MP3 audio and MP4 video are attached to the summary email.

**Database:**
- `DATABASE_URL` - PostgreSQL connection string

**Email Filtering:**
- `EMAIL_WHITELIST` - Comma-separated list of sender domains to process (e.g., `tldrnewsletter,morningbrew`)

## Development

### Running Locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### VS Code

The project includes launch configs. Hit F5 and pick:
- **Docker: Newsly API** - Runs in container
- **Local: Newsly API** - Runs directly with Python

### Tests

```bash
pytest tests/ -v
```

## API Endpoints

All endpoints except health check require API key authentication via the `X-API-Key` header.

- `POST /api/v1/email/new` - Gmail webhook endpoint (receives PubSub notifications)
- `POST /api/v1/email/send` - Manually trigger summary generation
- `GET /api/v1/health` - Health check (no auth required)

Example request:
```bash
curl -X POST "http://localhost:8000/api/v1/email/send?period=morning" \
  -H "X-API-Key: your-api-key-here"
```

## Project Structure

```
app/
├── api/v1/endpoints/   # Route handlers
├── core/               # Config, dependencies, exceptions
├── db/                 # Database models and repository
├── integrations/       # External services
│   ├── gmail/          # Gmail API client
│   ├── ai/             # Grok summarization
│   ├── tts/            # Text-to-speech (ElevenLabs)
│   └── video/          # Video generation with subtitles (FFmpeg)
├── schemas/            # Pydantic models
└── services/           # Business logic
```
