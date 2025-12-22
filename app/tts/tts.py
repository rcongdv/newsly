from app.tts.elevenlabs import text_to_speech
from app.tts.pytts import text_to_speech


class TTSServiceFactory:

    @staticmethod
    def _get_service(service_name: str):
        if service_name == "elevenlabs":
            return text_to_speech
        else:
            return text_to_speech
        
    def text_to_speech(self, service_name: str, text: str):
        service = self._get_service(service_name)
        return service.text_to_speech(text)