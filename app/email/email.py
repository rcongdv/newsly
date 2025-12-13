import json
import logging
import os

from app.email.gmail_auth import GmailAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

email_service = None


def get_email_service():
    global email_service
    if email_service is None:
        email_service = Email()
    return email_service


class Email:

    CLIENT_ID = os.getenv("GOOGLE_AUTH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_AUTH_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("GOOGLE_AUTH_REFRESH_TOKEN")
    PUBSUB_TOPIC_NAME = os.getenv("GMAIL_PUBSUB_TOPIC_NAME")
    USER_ID = "me"

    _auth: GmailAuth | None = None

    def __init__(self):
        self._auth = GmailAuth()
        self.watch()

    def watch(self):
        try:
            creds = self._auth.get_credentials()

            gmail = build("gmail", "v1", credentials=creds)

            watch_request_body = {
                "topicName": self.PUBSUB_TOPIC_NAME,
                "labelIds": ["INBOX"],
            }

            response = (
                gmail.users()
                .watch(userId=self.USER_ID, body=watch_request_body)
                .execute()
            )

            print(f"Gmail watch established. Expires: {response.get('expiration')}")

            return {
                "status": "Watch established",
                "topic": self.PUBSUB_TOPIC_NAME,
                "details": response,
                "next_step": f"Ensure Pub/Sub subscription is set to push to your webhook: /api/v1/pubsub/webhook",
            }

        except HttpError as e:
            error_details = json.loads(e.content.decode())
            error_message = f"Gmail Watch API Error: {error_details.get('error', {}).get('message', str(e))}"
            print(f"ERROR: {error_message}")
            raise RuntimeError(error_message) from e
        except Exception as e:
            error_message = f"An unexpected error occurred during watch setup: {e}"
            print(f"ERROR: {error_message}")
            raise RuntimeError(error_message) from e

    def process_email_webhook(self):
        try:
            latest_email = self._fetch_latest_email()

            return {
                "status": "processed",
                "latest_email": latest_email,
            }
        except Exception as e:
            error_message = f"Error processing webhook: {e}"
            print(f"ERROR: {error_message}")
            raise RuntimeError(error_message) from e

    def _fetch_latest_email(self):
        try:
            creds = self._auth.get_credentials()
            gmail = build("gmail", "v1", credentials=creds)

            results = (
                gmail.users()
                .messages()
                .list(userId="me", labelIds=["INBOX"], maxResults=1)
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                return None

            message = (
                gmail.users()
                .messages()
                .get(userId="me", id=messages[0]["id"])
                .execute()
            )

            headers = message["payload"].get("headers", [])
            email_info = {
                "id": messages[0]["id"],
                "snippet": message.get("snippet", ""),
            }

            for header in headers:
                if header["name"] == "From":
                    email_info["from"] = header["value"]
                elif header["name"] == "Subject":
                    email_info["subject"] = header["value"]
                elif header["name"] == "Date":
                    email_info["date"] = header["value"]

            return email_info

        except HttpError as e:
            print(f"Error fetching email: {e}")
            raise
