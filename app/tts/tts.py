import os

from app.tts.elevenlabs import get_elevenlabs_service
from app.tts.pytts import get_pytts_service


class TTSServiceFactory:

    @staticmethod
    def get_service(service_name: str):
        if service_name == "elevenlabs":
            return get_elevenlabs_service()
        else:
            return get_pytts_service()
        
    @staticmethod
    def text_to_speech(text: str):
        service_name = os.getenv("TTS_PROVIDER")
        service = TTSServiceFactory.get_service(service_name)
        return service.text_to_speech(text)