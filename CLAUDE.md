# Newsly

Newsletter-to-audio service. Fetches emails from Gmail, summarizes with Grok AI, converts to speech, sends back via email.

## Stack

- Python 3.12, FastAPI, async SQLAlchemy with PostgreSQL
- Grok (xai_sdk) for AI summarization
- TTS: PyTTS, ElevenLabs, Piper, Coqui TTS, Google Cloud TTS
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
│   └── tts/             # TTS factory + providers (pytts, elevenlabs, piper, coqui, google_tts)
├── schemas/             # Pydantic request/response models
├── services/            # Business logic (summary_generator.py)
└── main.py              # FastAPI app entrypoint
```

## Patterns

- **Factory pattern** for TTS providers (`TTSFactory.create()`)
- **Repository pattern** for database access (`EmailRepository`)
- **Dependency injection** via FastAPI's `Depends()`
- **Protocol classes** for TTS service interface

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
- `app/integrations/gmail/client.py` - Gmail API wrapper

## Notes

- **TTS providers**: PyTTS uses espeak-ng on Linux (robotic). For better quality in Docker, use Piper (lightweight neural), Coqui (voice cloning), ElevenLabs, or Google Cloud TTS.
- Database uses asyncpg with connection pooling (PGBouncer compatible).
- Gmail uses OAuth2 with refresh tokens. Run `scripts/generate_refresh_token.py` to get one.
- Email filtering via `EMAIL_WHITELIST` env var (comma-separated sender domains).

## Guidelines

- **Keep README.md updated** when making changes that affect:
  - New or removed API endpoints
  - New environment variables
  - Changes to project structure
  - New dependencies or setup steps
  - Changes to how the app is run or deployed

- **Write tests for new code**:
  - New features and integrations must have corresponding tests in `tests/`
  - Follow existing test patterns (see `test_elevenlabs.py`, `test_pytts.py` for examples)
  - Use mocks for external services - no real API calls in tests
  - Test both success paths and error handling
  - Include tests for factory functions that create services from settings
