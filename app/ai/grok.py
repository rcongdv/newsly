import logging
from pathlib import Path

from xai_sdk import Client
from xai_sdk.chat import user, system

from app.config import get_settings

logger = logging.getLogger(__name__)

grok_service = None


def get_grok_service():
    global grok_service
    if grok_service is None:
        grok_service = Grok()
    return grok_service


class Grok:

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.grok_api_key
        self.model = settings.grok_model

        prompt_path = Path(__file__).parent / "system_prompt.md"
        self.system_prompt = prompt_path.read_text().strip()

        if settings.tts_language == "ch":
            self.system_prompt += "\nRespond in Mandarin Chinese."

        if not self.api_key:
            raise ValueError(
                "Missing required GROK_API_KEY environment variable. Cannot initialize Grok service."
            )
        self.client = Client(api_key=self.api_key)
        self.chat = self.client.chat.create(
            model=self.model, messages=[system(self.system_prompt)]
        )

    def prompt(self, prompt: str) -> str:
        logger.info(f"Sending prompt to Grok API")
        self.chat.append(user(prompt))
        response = self.chat.sample()
        logger.info(f"Received response from Grok API: {response}")
        return response
