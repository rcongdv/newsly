import logging
import os
from pathlib import Path

from xai_sdk import Client
from xai_sdk.chat import user, system

logger = logging.getLogger(__name__)

grok_service = None


def get_grok_service():
    global grok_service
    if grok_service is None:
        grok_service = Grok()
    return grok_service


class Grok:

    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY")
        self.model = os.getenv("GROK_MODEL", "grok-3-mini")

        prompt_path = Path(__file__).parent / "system_prompt.md"
        if prompt_path.exists():
            self.system_prompt = prompt_path.read_text().strip()
        else:
            logger.warning(f"System prompt file not found at {prompt_path}. Using default.")
            self.system_prompt = "You are an expert AI assistant."

        if not self.api_key:
            raise ValueError(
                "Missing required GROK_API_KEY environment variable. Cannot initialize Grok service."
            )
        self.client = Client(api_key=self.api_key)
        self.chat = self.client.chat.create(
            model=self.model, messages=[system(self.system_prompt)]
        )

    def prompt(self, prompt: str) -> str:
        logger.info(f"Sending prompt to Grok API: {prompt}")
        self.chat.append(user(prompt))
        response = self.chat.sample()
        logger.info(f"Received response from Grok API: {response}")
        return response
