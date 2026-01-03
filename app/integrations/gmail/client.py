"""Gmail API client for fetching and sending emails."""

import base64
import json
import logging
import mimetypes
import re
from datetime import datetime, timezone, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import Settings
from app.core.exceptions import GmailServiceError
from app.integrations.gmail.auth import GmailAuth
from app.schemas.email import EmailData

logger = logging.getLogger(__name__)


class GmailClient:
    """Gmail API client for email operations."""

    USER_ID = "me"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        pubsub_topic: str,
    ):
        self._auth = GmailAuth(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )
        self._pubsub_topic = pubsub_topic

    def _get_gmail_service(self):
        """Get Gmail API service instance."""
        creds = self._auth.get_credentials()
        return build("gmail", "v1", credentials=creds)

    def watch(self) -> dict:
        """Set up Gmail watch for new emails via Pub/Sub."""
        try:
            gmail = self._get_gmail_service()

            watch_request_body = {
                "topicName": self._pubsub_topic,
                "labelIds": ["INBOX"],
            }

            response = (
                gmail.users()
                .watch(userId=self.USER_ID, body=watch_request_body)
                .execute()
            )

            expiration_ms = int(response.get("expiration"))
            expiration_pst = datetime.fromtimestamp(
                expiration_ms / 1000, tz=timezone(timedelta(hours=-8))
            )
            logger.info(
                f"Gmail watch established. Expires: {expiration_pst.strftime('%Y-%m-%d %I:%M:%S %p PST')}"
            )

            return {
                "status": "Watch established",
                "topic": self._pubsub_topic,
                "details": response,
            }

        except HttpError as e:
            error_details = json.loads(e.content.decode())
            error_message = error_details.get("error", {}).get("message", str(e))
            logger.error(f"Gmail Watch API Error: {error_message}")
            raise GmailServiceError(
                "Failed to set up Gmail watch",
                detail=error_message,
            ) from e
        except Exception as e:
            logger.exception("Unexpected error during watch setup")
            raise GmailServiceError(
                "Unexpected error during watch setup",
                detail=str(e),
            ) from e

    def fetch_latest_email(self) -> EmailData | None:
        """Fetch the most recent email from inbox."""
        try:
            gmail = self._get_gmail_service()

            results = (
                gmail.users()
                .messages()
                .list(userId=self.USER_ID, labelIds=["INBOX"], maxResults=1)
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                return None

            message = (
                gmail.users()
                .messages()
                .get(userId=self.USER_ID, id=messages[0]["id"])
                .execute()
            )

            headers = message["payload"].get("headers", [])
            email_data = {
                "gmail_id": messages[0]["id"],
            }

            for header in headers:
                if header["name"] == "From":
                    sender_name, sender_email = self._parse_sender(header["value"])
                    email_data["sender_name"] = sender_name
                    email_data["sender_email"] = sender_email
                elif header["name"] == "Subject":
                    email_data["subject"] = header["value"]
                elif header["name"] == "Date":
                    email_data["email_date"] = self._parse_date(header["value"])

            # Extract email body (HTML preferred, fallback to plain text)
            body_html, body_text = self._extract_body(message["payload"])
            email_data["body_html"] = body_html
            email_data["body_text"] = body_text

            return EmailData(**email_data)

        except HttpError as e:
            logger.error(f"Error fetching email: {e}")
            raise GmailServiceError(
                "Failed to fetch email",
                detail=str(e),
            ) from e

    def _extract_body(self, payload: dict) -> tuple[str | None, str | None]:
        """Extract HTML and plain text body from email payload."""
        body_html = None
        body_text = None

        def decode_body(data: str) -> str:
            return base64.urlsafe_b64decode(data).decode("utf-8")

        def find_parts(part: dict):
            nonlocal body_html, body_text

            mime_type = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data")

            if data:
                if mime_type == "text/html":
                    body_html = decode_body(data)
                elif mime_type == "text/plain":
                    body_text = decode_body(data)

            for sub_part in part.get("parts", []):
                find_parts(sub_part)

        find_parts(payload)
        return body_html, body_text

    def _parse_sender(self, from_header: str) -> tuple[str | None, str | None]:
        """Parse the From header into name and email."""
        if not from_header:
            return None, None

        match = re.match(r'^(?:"?([^"<]*)"?\s*)?<([^>]+)>$', from_header.strip())
        if match:
            name = match.group(1).strip() if match.group(1) else None
            email = match.group(2).strip()
            return name, email

        if "@" in from_header:
            return None, from_header.strip()

        return None, None

    def _parse_date(self, date_header: str) -> datetime | None:
        """Parse RFC 2822 date header into datetime object."""
        if not date_header:
            return None

        try:
            return parsedate_to_datetime(date_header)
        except Exception:
            return None

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body_html: str | None = None,
        body_text: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        attachments: list[str | Path] | None = None,
    ) -> dict:
        """Send an email via Gmail API."""
        try:
            gmail = self._get_gmail_service()

            # Create message
            if attachments:
                message = MIMEMultipart("mixed")
                body_part = MIMEMultipart("alternative")

                if body_text:
                    body_part.attach(MIMEText(body_text, "plain"))
                if body_html:
                    body_part.attach(MIMEText(body_html, "html"))

                message.attach(body_part)

                # Add attachments
                for file_path in attachments:
                    file_path = Path(file_path)
                    if not file_path.exists():
                        raise FileNotFoundError(f"Attachment not found: {file_path}")

                    content_type, _ = mimetypes.guess_type(str(file_path))
                    if content_type is None:
                        content_type = "application/octet-stream"

                    main_type, sub_type = content_type.split("/", 1)

                    with open(file_path, "rb") as f:
                        attachment = MIMEBase(main_type, sub_type)
                        attachment.set_payload(f.read())

                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=file_path.name,
                    )
                    message.attach(attachment)
            else:
                message = MIMEMultipart("alternative")
                if body_text:
                    message.attach(MIMEText(body_text, "plain"))
                if body_html:
                    message.attach(MIMEText(body_html, "html"))

            # Set headers
            to_str = ", ".join(to) if isinstance(to, list) else to
            message["To"] = to_str
            message["Subject"] = subject

            if cc:
                cc_str = ", ".join(cc) if isinstance(cc, list) else cc
                message["Cc"] = cc_str

            if bcc:
                bcc_str = ", ".join(bcc) if isinstance(bcc, list) else bcc
                message["Bcc"] = bcc_str

            # Encode and send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            result = (
                gmail.users()
                .messages()
                .send(userId=self.USER_ID, body={"raw": raw})
                .execute()
            )

            logger.info(f"Email sent successfully. Message ID: {result.get('id')}")

            return {
                "message_id": result.get("id"),
                "thread_id": result.get("threadId"),
            }

        except HttpError as e:
            error_details = json.loads(e.content.decode())
            error_message = error_details.get("error", {}).get("message", str(e))
            logger.error(f"Gmail Send API Error: {error_message}")
            raise GmailServiceError(
                "Failed to send email",
                detail=error_message,
            ) from e
        except Exception as e:
            logger.exception("Error sending email")
            raise GmailServiceError(
                "Error sending email",
                detail=str(e),
            ) from e


def create_gmail_client(settings: Settings) -> GmailClient:
    """Factory function to create GmailClient from settings."""
    return GmailClient(
        client_id=settings.google_auth_client_id,
        client_secret=settings.google_auth_client_secret,
        refresh_token=settings.google_auth_refresh_token,
        pubsub_topic=settings.gmail_pubsub_topic_name,
    )
