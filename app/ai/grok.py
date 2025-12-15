import logging
import os
from pathlib import Path

from xai_sdk import Client
from xai_sdk.chat import user, system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

grok_service = None


def get_grok_service():
    global grok_service
    if grok_service is None:
        grok_service = Grok()
    return grok_service


class Grok:

    API_KEY = os.getenv("GROK_API_KEY")
    MODEL = os.getenv("GROK_MODEL", "grok-3-mini")

    prompt_path = Path(__file__).parent / "system_prompt.md"
    if prompt_path.exists():
        SYSTEM_PROMPT = prompt_path.read_text().strip()
    else:
        logger.warning(f"System prompt file not found at {prompt_path}. Using default.")
        SYSTEM_PROMPT = "You are an expert AI assistant."

    chat = None

    def __init__(self):
        if not self.API_KEY:
            raise ValueError(
                "Missing required GROK_API_KEY environment variable. Cannot initialize Grok service."
            )
        self.client = Client(api_key=self.API_KEY)
        self.chat = self.client.chat.create(
            model=self.MODEL, messages=[system(self.SYSTEM_PROMPT)]
        )

    def prompt(self, prompt: str) -> str:
        logger.info(f"Sending prompt to Grok API: {prompt}")
        self.chat.append(user(prompt))
        response = self.chat.sample()
        logger.info(f"Received response from Grok API: {response}")
        return response
