import logging
import os

from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

elevenlabs_service = None


def get_elevenlabs_service():
    global elevenlabs_service
    if elevenlabs_service is None:
        elevenlabs_service = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )
    return elevenlabs_service


class ElevenLabsService:

    def __init__(self):
        self.elevenlabs = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )

    def text_to_speech(
        self, text: str, voice_id: str, model_id: str, output_format: str
    ):
        audio = self.elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
        )
        return audio
