# Newsly

Turns your newsletter emails into audio summaries. Connects to Gmail, uses Grok to summarize the content, converts it to speech, and emails you the audio file.

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run with Docker:

```bash
docker compose up --build
```

The API runs on `http://localhost:8000`.

### Environment Variables

**Google/Gmail:**
- `GOOGLE_AUTH_CLIENT_ID` / `GOOGLE_AUTH_CLIENT_SECRET` - OAuth credentials
- `GOOGLE_AUTH_REFRESH_TOKEN` - Run `scripts/generate_refresh_token.py` to get this
- `GMAIL_PUBSUB_TOPIC_NAME` - For Gmail push notifications

**AI:**
- `GROK_API_KEY` - Your X.AI API key
- `GROK_MODEL` - Model to use (defaults to latest)

**TTS:**
- `TTS_PROVIDER` - One of: `pytts`, `elevenlabs`, `piper`, `coqui`, `google`
- `TTS_OUTPUT_FORMAT` - `mp3`, `wav`, etc.
- `TTS_LANGUAGE` - Language code (default: `en`)

Provider-specific settings:

| Provider | Variables | Notes |
|----------|-----------|-------|
| `pytts` | `PYTTS_VOICE_RATE`, `PYTTS_VOLUME`, `PYTTS_VOICE_ID` | Local, uses system TTS. Robotic on Linux (espeak). |
| `elevenlabs` | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID` | Cloud, high quality, paid API. |
| `piper` | `PIPER_MODEL_PATH`, `PIPER_SPEAKER_ID`, `PIPER_LENGTH_SCALE`, `PIPER_SENTENCE_SILENCE` | Local neural TTS, lightweight, good quality. |
| `coqui` | `COQUI_MODEL_NAME`, `COQUI_SPEAKER_WAV`, `COQUI_USE_GPU` | Local neural TTS, supports voice cloning. Large dependency (PyTorch). |
| `google` | `GOOGLE_TTS_CREDENTIALS_PATH`, `GOOGLE_TTS_LANGUAGE_CODE`, `GOOGLE_TTS_VOICE_NAME`, `GOOGLE_TTS_VOICE_GENDER`, `GOOGLE_TTS_SPEAKING_RATE`, `GOOGLE_TTS_PITCH` | Cloud, high quality, pay-per-use. |

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

- `POST /api/v1/email/new` - Gmail webhook endpoint (receives PubSub notifications)
- `POST /api/v1/email/send` - Manually trigger summary generation
- `GET /api/v1/health` - Health check

## Project Structure

```
app/
├── api/v1/endpoints/   # Route handlers
├── core/               # Config, dependencies, exceptions
├── db/                 # Database models and repository
├── integrations/       # External services
│   ├── gmail/          # Gmail API client
│   ├── ai/             # Grok summarization
│   └── tts/            # Text-to-speech (PyTTS, ElevenLabs, Piper, Coqui, Google)
├── schemas/            # Pydantic models
└── services/           # Business logic
```
