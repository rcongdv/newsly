import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.email.email import get_email_service
from app.db import init_db, async_session, EmailRepository
from app.ai.grok import get_grok_service
from app.ai.elevenlabs import get_elevenlabs_service


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    yield

    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/email/new")
async def process_email_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")

        email_service = get_email_service()
        result = email_service.process_email_webhook()

        latest_email = result.get("latest_email")

        grok = get_grok_service()
        prompt = f"{latest_email.get('body_html')}"
        response = grok.prompt(prompt)
        logger.info(f"Grok response: {response}")

        if latest_email:
            async with async_session() as session:
                repo = EmailRepository(session)
                db_email, created = await repo.create_if_not_exists(
                    gmail_id=latest_email.get("id"),
                    sender_name=latest_email.get("sender_name"),
                    sender_email=latest_email.get("sender_email"),
                    subject=latest_email.get("subject"),
                    snippet=latest_email.get("snippet"),
                    body_html=latest_email.get("body_html"),
                    body_text=latest_email.get("body_text"),
                    ai_summary=response,
                    email_date=latest_email.get("date"),
                )
                logger.info(
                    f"Email {'created' if created else 'already exists'}: {db_email.gmail_id}"
                )

        elevenlabs = get_elevenlabs_service()
        tts_audio = elevenlabs.text_to_speech(
            text=response,
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_monolingual_v1",
            output_format="mp3",
        )
        with open("output.mp3", "wb") as audio_file:
            audio_file.write(tts_audio)
            logger.info("Text-to-speech audio saved as output.mp3")

        return {
            "message": "Email webhook received and processed.",
            "email": result,
            "grok_response": response,
        }
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}")
        return {"error": "Failed to process email webhook."}, 500


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
