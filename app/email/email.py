import base64
import json
import logging
import os
from datetime import datetime, timezone, timedelta


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

            expiration_ms = int(response.get('expiration'))
            expiration_pst = datetime.fromtimestamp(expiration_ms / 1000, tz=timezone(timedelta(hours=-8)))
            print(f"Gmail watch established. Expires: {expiration_pst.strftime('%Y-%m-%d %I:%M:%S %p PST')}")

            return {
                "status": "Watch established",
                "topic": self.PUBSUB_TOPIC_NAME,
                "details": response,
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

            # Extract email body (HTML preferred, fallback to plain text)
            body_html, body_text = self._extract_body(message["payload"])
            email_info["body_html"] = body_html
            email_info["body_text"] = body_text

            return email_info

        except HttpError as e:
            print(f"Error fetching email: {e}")
            raise

    def _extract_body(self, payload: dict) -> tuple[str | None, str | None]:
        """
        Extract HTML and plain text body from email payload.
        Returns (body_html, body_text) tuple.
        """
        body_html = None
        body_text = None

        def decode_body(data: str) -> str:
            """Decode base64url encoded body data."""
            return base64.urlsafe_b64decode(data).decode("utf-8")

        def find_parts(part: dict):
            """Recursively find text/html and text/plain parts."""
            nonlocal body_html, body_text

            mime_type = part.get("mimeType", "")

            # Check if this part has body data
            body = part.get("body", {})
            data = body.get("data")

            if data:
                if mime_type == "text/html":
                    body_html = decode_body(data)
                elif mime_type == "text/plain":
                    body_text = decode_body(data)

            # Recursively check nested parts
            for sub_part in part.get("parts", []):
                find_parts(sub_part)

        find_parts(payload)
        return body_html, body_text
