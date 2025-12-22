import os

from app.tts.elevenlabs import text_to_speech as elevenlabs_tts
from app.tts.pytts import text_to_speech as pytts_tts


class TTSServiceFactory:

    @staticmethod
    def _get_service(service_name: str):
        if service_name == "elevenlabs":
            return elevenlabs_tts
        else:
            return pytts_tts
        
    def text_to_speech(self, text: str):
        service_name = os.getenv("TTS_VENDOR")
        service = self._get_service(service_name)
        return service(text)