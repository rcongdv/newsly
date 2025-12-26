import logging
import sys
import uvicorn
from datetime import date, time, datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.config import get_settings
from app.db import get_database, EmailRepository
from app.email import get_email_service
from app.ai import get_grok_service
from app.tts.tts import TTSServiceFactory

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
    logger.info("Health check requested")
    return {"status": "healthy"}


@app.post("/api/v1/email/new")
async def process_new_event(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received new email: {data}")

        email_service = get_email_service()
        result = email_service.process_new_event()

        latest_email = result.get("latest_email")

        async with get_database().async_session() as session:
            repo = EmailRepository(session)

            if latest_email and latest_email.get("id"):

                if await repo.get_by_gmail_id(latest_email.get("id")):
                    logger.info(f"Email already exists in DB: {latest_email.get('id')}")
                    return {"message": "Email already processed"}

                await repo.create(
                    gmail_id=latest_email.get("id"),
                    sender_name=latest_email.get("sender_name"),
                    sender_email=latest_email.get("sender_email"),
                    subject=latest_email.get("subject"),
                    body_html=latest_email.get("body_html"),
                    body_text=latest_email.get("body_text"),
                    email_date=latest_email.get("email_date"),
                )

                return {"message": "New event received and processed"}

            return {"message": "No email to process"}
    except Exception as e:
        logger.error(f"Error processing new event: {e}")
        return {"error": "Failed to process new event", "status_code": 500}


@app.post("/api/v1/email/send")
async def trigger_grok(request: Request):
    try:
        period = request.query_params.get("period", "morning")
        logger.info(f"Triggering email sending for period: {period}")

        settings = get_settings()
        time_frame = settings.time_frames.get(period)
        time_format = settings.time_format

        async with get_database().async_session() as session:
            repo = EmailRepository(session)

            start_date = datetime.combine(
                date.today(), datetime.strptime(time_frame[0], time_format).time()
            )
            end_date = datetime.combine(
                date.today(), datetime.strptime(time_frame[1], time_format).time()
            )
            emails = await repo.get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                allowed_domains=settings.email_domain_whitelist_list,
            )

            emails_text = "\n\nNEXT EMAIL:\n\n".join(
                email.body_html for email in emails
            )

            grok = get_grok_service()
            response = grok.prompt(emails_text)

            TTSServiceFactory.text_to_speech(response.content)

            email_service = get_email_service()

            email_service.send_email(
                to="richardcong635@gmail.com",
                subject="",
                body_text=response.content,
                attachments=[settings.tts_output_path],
            )
        return {"message": "Email sending triggered"}
    except Exception as e:
        logger.error(f"Error triggering email sending: {e}")
        return {"error": "Failed to trigger email sending", "status_code": 500}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
