import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone
from googleapiclient.errors import HttpError
from app.integrations.gmail.client import GmailClient, create_gmail_client
from app.core.exceptions import GmailServiceError


class TestGmailClient:
    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock()
        settings.google_auth_client_id = "test-client-id"
        settings.google_auth_client_secret = "test-secret"
        settings.google_auth_refresh_token = "test-refresh-token"
        settings.gmail_pubsub_topic_name = "test-topic"
        return settings

    @pytest.fixture
    def gmail_client(self, mock_settings):
        with patch("app.integrations.gmail.client.GmailAuth"):
            return GmailClient(
                client_id=mock_settings.google_auth_client_id,
                client_secret=mock_settings.google_auth_client_secret,
                refresh_token=mock_settings.google_auth_refresh_token,
                pubsub_topic=mock_settings.gmail_pubsub_topic_name,
            )

    @patch("app.integrations.gmail.client.build")
    def test_watch_success(self, mock_build, gmail_client):
        # Setup mock service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_watch_response = {
            "expiration": "1678886400000",  # Timestamp in ms
            "historyId": "12345",
        }
        mock_service.users().watch().execute.return_value = mock_watch_response

        # Execute
        result = gmail_client.watch()

        # Verify
        assert result["status"] == "Watch established"
        assert result["topic"] == "test-topic"
        assert result["details"] == mock_watch_response
        mock_service.users().watch.assert_called_with(
            userId="me", body={"topicName": "test-topic", "labelIds": ["INBOX"]}
        )

    @patch("app.integrations.gmail.client.build")
    def test_watch_failure(self, mock_build, gmail_client):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock HttpError
        error_content = b'{"error": {"message": "Permission denied"}}'
        error = HttpError(resp=MagicMock(status=403), content=error_content)
        mock_service.users().watch().execute.side_effect = error

        with pytest.raises(GmailServiceError) as exc:
            gmail_client.watch()

        assert "Permission denied" in exc.value.detail

    @patch("app.integrations.gmail.client.build")
    def test_fetch_latest_email_empty(self, mock_build, gmail_client):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Return empty list
        mock_service.users().messages().list().execute.return_value = {}

        result = gmail_client.fetch_latest_email()
        assert result is None

    @patch("app.integrations.gmail.client.build")
    def test_fetch_latest_email_success(self, mock_build, gmail_client):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock list response
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg-123"}]
        }

        # Mock get message response
        mock_message = {
            "id": "msg-123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Test User <test@example.com>"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "Wed, 15 Mar 2023 10:00:00 +0000"},
                ],
                "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World" in base64
                "mimeType": "text/plain",
            },
        }
        mock_service.users().messages().get().execute.return_value = mock_message

        result = gmail_client.fetch_latest_email()

        assert result.gmail_id == "msg-123"
        assert result.sender_name == "Test User"
        assert result.sender_email == "test@example.com"
        assert result.subject == "Test Subject"
        assert result.body_text == "Hello World"

    @patch("app.integrations.gmail.client.build")
    def test_send_email_simple(self, mock_build, gmail_client):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().send().execute.return_value = {
            "id": "sent-123",
            "threadId": "thread-123",
        }

        result = gmail_client.send_email(
            to="recipient@example.com", subject="Test Subject", body_text="Test Body"
        )

        assert result["message_id"] == "sent-123"

        # Verify call arguments
        call_args = mock_service.users().messages().send.call_args
        assert call_args is not None
        body = call_args[1]["body"]
        assert "raw" in body

    def test_parse_sender_formats(self, gmail_client):
        # Test "Name <email>" format
        name, email = gmail_client._parse_sender("John Doe <john@example.com>")
        assert name == "John Doe"
        assert email == "john@example.com"

        # Test "email" format (no name)
        name, email = gmail_client._parse_sender("john@example.com")
        assert name is None
        assert email == "john@example.com"

        # Test "<email>" format
        name, email = gmail_client._parse_sender("<john@example.com>")
        assert name is None
        assert email == "john@example.com"

        # Test complex name
        name, email = gmail_client._parse_sender('"Doe, John" <john@example.com>')
        assert name == "Doe, John"
        assert email == "john@example.com"

    def test_extract_body_html_preferred(self, gmail_client):
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": "UGxhaW4="},  # "Plain"
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": "PEhUTUw+"},  # "<HTML>"
                },
            ],
        }

        html, text = gmail_client._extract_body(payload)
        assert html == "<HTML>"
        assert text == "Plain"

    def test_create_gmail_client_factory(self, mock_settings):
        with patch("app.integrations.gmail.client.GmailAuth"):
            client = create_gmail_client(mock_settings)
            assert isinstance(client, GmailClient)
