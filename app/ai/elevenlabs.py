import logging
import os

from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

logger = logging.getLogger(__name__)

elevenlabs_service = None


def get_elevenlabs_service():
    global elevenlabs_service
    if elevenlabs_service is None:
        elevenlabs_service = ElevenLabsService()
    return elevenlabs_service


class ElevenLabsService:

    def __init__(self):
        self.elevenlabs = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )
        self.ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
        self.ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID")

    def text_to_speech(self, text: str, output_format: str) -> bytes:
        audio_generator = self.elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=self.ELEVENLABS_VOICE_ID,
            model_id=self.ELEVENLABS_MODEL_ID,
            output_format=output_format,
        )
        return b"".join(audio_generator)
