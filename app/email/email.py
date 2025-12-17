import base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime
from email import encoders
import json
import logging
import mimetypes
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.email.gmail_auth import GmailAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


logger = logging.getLogger(__name__)

email_service = None


def get_email_service():
    global email_service
    if email_service is None:
        email_service = Email()
    return email_service


class Email:

    USER_ID = "me"

    def __init__(self):
        self.pubsub_topic_name = os.getenv("GMAIL_PUBSUB_TOPIC_NAME")
        self._auth = GmailAuth()
        self.watch()

    def watch(self):
        try:
            creds = self._auth.get_credentials()

            gmail = build("gmail", "v1", credentials=creds)

            watch_request_body = {
                "topicName": self.pubsub_topic_name,
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
            print(
                f"Gmail watch established. Expires: {expiration_pst.strftime('%Y-%m-%d %I:%M:%S %p PST')}"
            )

            return {
                "status": "Watch established",
                "topic": self.pubsub_topic_name,
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

    def process_new_email(self):
        try:
            latest_email = self._fetch_latest_email()

            return {
                "status": "processed",
                "latest_email": latest_email,
            }
        except Exception as e:
            error_message = f"Error processing new email: {e}"
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
                    sender_name, sender_email = self._parse_sender(header["value"])
                    email_info["sender_name"] = sender_name
                    email_info["sender_email"] = sender_email
                elif header["name"] == "Subject":
                    email_info["subject"] = header["value"]
                elif header["name"] == "Date":
                    email_info["date"] = self._parse_date(header["value"])

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

    def _parse_sender(self, from_header: str) -> tuple[str | None, str | None]:
        """
        Parse the From header into name and email.
        Handles formats like:
        - "John Doe <john@example.com>"
        - "<john@example.com>"
        - "john@example.com"
        """
        if not from_header:
            return None, None

        # Match "Name <email>" or "<email>" format
        match = re.match(r'^(?:"?([^"<]*)"?\s*)?<([^>]+)>$', from_header.strip())
        if match:
            name = match.group(1).strip() if match.group(1) else None
            email = match.group(2).strip()
            return name, email

        # Plain email address
        if "@" in from_header:
            return None, from_header.strip()

        return None, None

    def _parse_date(self, date_header: str) -> datetime | None:
        """
        Parse RFC 2822 date header into datetime object.
        Example: "Sat, 14 Dec 2024 10:30:00 +0000"
        """
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
        """
        Send an email via Gmail API.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content (fallback)
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            attachments: List of file paths to attach

        Returns:
            dict with message id and thread id
        """
        try:
            creds = self._auth.get_credentials()
            gmail = build("gmail", "v1", credentials=creds)

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
            error_message = f"Gmail Send API Error: {error_details.get('error', {}).get('message', str(e))}"
            logger.error(error_message)
            raise RuntimeError(error_message) from e
        except Exception as e:
            error_message = f"Error sending email: {e}"
            logger.error(error_message)
            raise RuntimeError(error_message) from e
