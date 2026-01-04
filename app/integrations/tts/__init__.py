from app.integrations.tts.base import TTSService, BaseTTSService
from app.integrations.tts.factory import TTSFactory
from app.integrations.tts.elevenlabs import ElevenLabsService, create_elevenlabs_service
from app.integrations.tts.pytts import PyTTSService, create_pytts_service
from app.integrations.tts.piper import PiperService, create_piper_service
from app.integrations.tts.google_tts import GoogleTTSService, create_google_tts_service

# Coqui TTS is optional - import lazily to avoid requiring TTS library
# from app.integrations.tts.coqui import CoquiService, create_coqui_service

__all__ = [
    "TTSService",
    "BaseTTSService",
    "TTSFactory",
    "ElevenLabsService",
    "create_elevenlabs_service",
    "PyTTSService",
    "create_pytts_service",
    "PiperService",
    "create_piper_service",
    "GoogleTTSService",
    "create_google_tts_service",
]
