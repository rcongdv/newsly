import logging
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.db import get_database, EmailRepository
from app.email import get_email_service
from app.ai import get_grok_service, get_elevenlabs_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger().handlers[0].flush = sys.stdout.flush
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    logger.info("Initializing database...")
    await get_database().init_db()
    logger.info("Database initialized.")

    yield

    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/email/new")
async def process_new_email(request: Request):
    try:
        data = await request.json()
        logger.info(f"Endpoint called, data: {data}")

        email_service = get_email_service()
        result = email_service.process_new_email()

        latest_email = result.get("latest_email")

        grok = get_grok_service()
        prompt = f"{latest_email.get('body_html')}"
        response = grok.prompt(prompt)
        logger.info(f"Grok response: {response}")

        if latest_email:
            async with get_database().async_session() as session:
                repo = EmailRepository(session)
                db_email, created = await repo.create_if_not_exists(
                    gmail_id=latest_email.get("id"),
                    sender_name=latest_email.get("sender_name"),
                    sender_email=latest_email.get("sender_email"),
                    subject=latest_email.get("subject"),
                    snippet=latest_email.get("snippet"),
                    body_html=latest_email.get("body_html"),
                    body_text=latest_email.get("body_text"),
                    ai_summary=response.content,
                    email_date=latest_email.get("date"),
                )
                logger.info(
                    f"Email {'created' if created else 'already exists'}: {db_email.gmail_id}"
                )

        elevenlabs = get_elevenlabs_service()
        tts_audio = elevenlabs.text_to_speech(
            text=response.content,
            output_format="mp3_44100_128",
        )
        with open("output.mp3", "wb") as audio_file:
            audio_file.write(tts_audio)
        logger.info("Text-to-speech audio saved as output.mp3")

        email_service.send_email(
            to="richardcong635@gmail.com",
            subject=latest_email.get("subject"),
            body_text=response.content,
            attachments=["output.mp3"],
        )

        return {"message": "New email received and processed"}
    except Exception as e:
        logger.error(f"Error processing new email: {e}")
        return {"error": "Failed to process new email"}, 500


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
