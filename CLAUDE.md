# Newsly

Newsletter-to-audio service. Fetches emails from Gmail, summarizes with Grok AI, converts to speech, sends back via email.

## Stack

- Python 3.12, FastAPI, async SQLAlchemy with PostgreSQL
- Grok (xai_sdk) for AI summarization
- TTS: PyTTS, ElevenLabs, Google Cloud TTS
- Video: FFmpeg with burned-in subtitles (optional)
- Gmail API for email fetch/send
- Deployed on Fly.io

## Project Layout

```
app/
├── api/v1/endpoints/    # FastAPI routes
├── core/                # config.py, dependencies.py, exceptions.py
├── db/                  # database.py, models.py, repository.py
├── integrations/
│   ├── gmail/           # Gmail API client
│   ├── ai/              # Grok service
│   ├── tts/             # TTS factory + providers (pytts, elevenlabs, google_tts)
│   └── video/           # Video generation with subtitles (ffmpeg)
├── schemas/             # Pydantic request/response models
├── services/            # Business logic (summary_generator.py)
└── main.py              # FastAPI app entrypoint
```

## Patterns

- **Factory pattern** for TTS providers (`TTSFactory.create()`) and video service (`VideoFactory.create()`)
- **Repository pattern** for database access (`EmailRepository`)
- **Dependency injection** via FastAPI's `Depends()`
- **Protocol classes** for TTS and video service interfaces

## Running

```bash
# Docker (preferred)
docker compose up --build

# Local
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest tests/ -v
```

All tests use mocks - no external services needed.

## Key Files

- `app/core/config.py` - All env vars and settings
- `app/services/summary_generator.py` - Main orchestration logic
- `app/integrations/tts/base.py` - TTS factory and protocol
- `app/integrations/video/base.py` - Video service protocol
- `app/integrations/video/ffmpeg_video.py` - FFmpeg video implementation
- `app/integrations/gmail/client.py` - Gmail API wrapper

## Notes

- **TTS providers**: PyTTS uses espeak-ng on Linux (robotic). For better quality in Docker, use ElevenLabs or Google Cloud TTS.
- **Video generation**: Optional feature that creates MP4 with burned-in subtitles. Enable with `VIDEO_ENABLED=true`. Uses FFmpeg (already in Dockerfile).
- Database uses asyncpg with connection pooling (PGBouncer compatible).
- Gmail uses OAuth2 with refresh tokens. Run `scripts/generate_refresh_token.py` to get one.
- Email filtering via `EMAIL_WHITELIST` env var (comma-separated sender domains).

## Guidelines

### Code Style
- Use type hints for function signatures
- Keep functions focused and single-purpose
- Prefer composition over inheritance

### Async Patterns
- All database operations must be async (use `await`)
- Use `async with` for database sessions
- Avoid blocking calls in async functions

### Error Handling
- Use custom exceptions from `app/core/exceptions.py`
- Let FastAPI exception handlers manage HTTP responses
- Log errors with appropriate context

### API Endpoints
- Place in `app/api/v1/endpoints/`
- Use Pydantic schemas for request/response validation
- Inject dependencies via `Depends()`

### Database Changes
- Models go in `app/db/models.py`
- Use repository pattern for queries (`app/db/repository.py`)
- Keep business logic out of models

### Environment Variables
- Define all env vars in `app/core/config.py` using Pydantic Settings
- Use descriptive names with appropriate prefixes (e.g., `GMAIL_`, `TTS_`)
- Document required vs optional variables

### Adding New TTS Providers
- Implement the `TTSService` protocol from `app/integrations/tts/base.py`
- Register in `TTSFactory.create()` method
- Add provider to `TTSProvider` enum in config
- Include corresponding tests

### Adding New Video Providers
- Implement the `VideoService` protocol from `app/integrations/video/base.py`
- Register in `VideoFactory.create()` method
- Include corresponding tests
- Follow the pattern established by `FFmpegVideoService`

### Testing
- New features and integrations must have corresponding tests in `tests/`
- Follow existing test patterns (see `test_elevenlabs.py`, `test_pytts.py` for examples)
- Use mocks for external services - no real API calls in tests
- Test both success paths and error handling
- Include tests for factory functions that create services from settings

### Documentation
- **Keep CLAUDE.md updated** when making changes that affect:
  - Project structure or layout
  - Architectural patterns or conventions
  - Key files and their purposes
  - Development guidelines or best practices
- **Keep README.md updated** when making changes that affect:
  - New or removed API endpoints
  - New environment variables
  - Changes to project structure
  - New dependencies or setup steps
  - Changes to how the app is run or deployed
