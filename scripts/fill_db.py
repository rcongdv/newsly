#!/usr/bin/env python3
"""
Script to fill the database with all emails from the connected Gmail account.
"""

import asyncio
import base64
import re
import sys
import traceback
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings
from app.db.database import get_database
from app.db.repositories.email import EmailRepository
from app.integrations.gmail.auth import GmailAuth


def list_all_message_ids(gmail) -> list[str]:
    """Fetch all message IDs from the inbox using pagination."""
    message_ids = []
    page_token = None

    while True:
        try:
            results = (
                gmail.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["INBOX"],
                    pageToken=page_token,
                    maxResults=500,
                )
                .execute()
            )

            messages = results.get("messages", [])
            for msg in messages:
                message_ids.append(msg["id"])

            page_token = results.get("nextPageToken")
            if not page_token:
                break

            print(f"  Fetched {len(message_ids)} message IDs so far...")

        except HttpError as e:
            print(f"Error listing messages: {e}")
            raise

    return message_ids


def parse_sender(from_header: str) -> tuple[str | None, str | None]:
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


def parse_date(date_header: str) -> datetime | None:
    """Parse RFC 2822 date header into datetime object."""
    if not date_header:
        return None

    try:
        return parsedate_to_datetime(date_header)
    except Exception:
        return None


def extract_body(payload: dict) -> tuple[str | None, str | None]:
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


def fetch_and_parse_email(gmail, message_id: str) -> dict:
    """Fetch a single email and parse its contents."""
    message = gmail.users().messages().get(userId="me", id=message_id).execute()

    headers = message["payload"].get("headers", [])
    email_data = {"gmail_id": message_id}

    for header in headers:
        name = header["name"]
        value = header["value"]

        if name == "From":
            sender_name, sender_email = parse_sender(value)
            email_data["sender_name"] = sender_name
            email_data["sender_email"] = sender_email
        elif name == "Subject":
            email_data["subject"] = value
        elif name == "Date":
            email_data["email_date"] = parse_date(value)

    body_html, body_text = extract_body(message["payload"])
    email_data["body_html"] = body_html
    email_data["body_text"] = body_text

    return email_data


async def main():
    print("Initializing Gmail connection...")
    settings = get_settings()
    auth = GmailAuth(
        client_id=settings.google_auth_client_id,
        client_secret=settings.google_auth_client_secret,
        refresh_token=settings.google_auth_refresh_token,
    )
    creds = auth.get_credentials()
    gmail = build("gmail", "v1", credentials=creds)

    print("Initializing database...")
    db = get_database()
    await db.init_db()

    print("Fetching all message IDs from inbox...")
    message_ids = list_all_message_ids(gmail)
    total = len(message_ids)
    print(f"Found {total} emails in inbox")

    if total == 0:
        print("No emails to process.")
        return

    new_count = 0
    existing_count = 0
    error_count = 0

    async with db.get_session()() as session:
        repo = EmailRepository(session)

        for i, message_id in enumerate(message_ids, 1):
            try:
                email_data = fetch_and_parse_email(gmail, message_id)

                _, created = await repo.create_if_not_exists(
                    gmail_id=email_data["gmail_id"],
                    sender_name=email_data.get("sender_name"),
                    sender_email=email_data.get("sender_email"),
                    subject=email_data.get("subject"),
                    body_html=email_data.get("body_html"),
                    body_text=email_data.get("body_text"),
                    email_date=email_data.get("email_date"),
                )

                if created:
                    new_count += 1
                else:
                    existing_count += 1

                if i % 50 == 0 or i == total:
                    print(
                        f"Progress: {i}/{total} "
                        f"({new_count} new, {existing_count} existing, {error_count} errors)"
                    )

            except HttpError as e:
                error_count += 1
                print(f"Error fetching email {message_id}: {e}")
                traceback.print_exc()
            except Exception as e:
                error_count += 1
                print(f"Error processing email {message_id}: {e}")
                traceback.print_exc()
                await session.rollback()

    print(f"\nDone! Processed {total} emails:")
    print(f"  - {new_count} new emails added")
    print(f"  - {existing_count} already existed")
    print(f"  - {error_count} errors")


if __name__ == "__main__":
    asyncio.run(main())
