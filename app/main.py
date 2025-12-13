import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from urllib3 import request

from app.email.email import get_email_service


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    yield

    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "TEST123"}


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/email/webhook")
async def process_email_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")

        email_service = get_email_service()
        email = email_service.process_email_webhook()

        logger.info(email)
        return {"message": "Email webhook received and processed."}
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}")
        return {"error": "Failed to process email webhook."}, 500


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
