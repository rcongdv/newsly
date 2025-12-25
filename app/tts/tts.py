from app.config import get_settings
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
        settings = get_settings()
        service = TTSServiceFactory.get_service(settings.tts_provider)
        return service.text_to_speech(text)