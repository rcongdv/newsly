"""Tests for the email endpoints in app.api.v1.endpoints.email."""

import pytest
from unittest.mock import AsyncMock, ANY

from app.schemas.email import TimePeriod
from tests.conftest import TEST_API_KEY


def test_send_summary_endpoint(client, mock_ai_service, mock_email_repo):
    """Test POST /api/v1/email/send endpoint with valid API key."""
    # Setup mock data
    mock_email_repo.get_by_date_range = AsyncMock(return_value=[])

    response = client.post(
        "/api/v1/email/send",
        params={"period": "morning", "recipient": "test@example.com"},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "No emails found, sent empty summary"
    assert data["emails_processed"] == 0


def test_send_summary_endpoint_missing_api_key(client):
    """Test POST /api/v1/email/send returns 401 without API key."""
    response = client.post(
        "/api/v1/email/send",
        params={"period": "morning"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid authentication"


def test_send_summary_endpoint_invalid_api_key(client):
    """Test POST /api/v1/email/send returns 401 with invalid API key."""
    response = client.post(
        "/api/v1/email/send",
        params={"period": "morning"},
        headers={"X-API-Key": "wrong-api-key"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid authentication"


def test_send_summary_endpoint_validation_error(client):
    """Test validation error for invalid period."""
    response = client.post(
        "/api/v1/email/send",
        params={"period": "invalid_period"},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 422


def test_send_summary_endpoint_invalid_recipient(client):
    """Test validation error for invalid recipient email."""
    response = client.post(
        "/api/v1/email/send",
        params={"period": "morning", "recipient": "not-an-email"},
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_webhook_endpoint(client, mock_email_repo, mock_gmail_client):
    """Test POST /api/v1/email/new webhook endpoint with valid API key."""
    from app.schemas.email import EmailData

    # Mock Gmail client response
    mock_gmail_client.fetch_latest_email.return_value = EmailData(
        gmail_id="123",
        sender_email="test@example.com",
        subject="Test email",
        body_text="Test body",
        email_date=None,
    )

    # Mock Repo response
    # create_if_not_exists returns (email_obj, created_bool)
    mock_email_repo.create_if_not_exists.return_value = (None, True)
    # create returns email_obj
    mock_email_repo.create.return_value = None
    # get_by_gmail_id returns None (not existing)
    mock_email_repo.get_by_gmail_id.return_value = None

    payload = {
        "message": {
            "data": "eyJlbWFpbEFkZHJlc3MiOiAidGVzdEBleGFtcGxlLmNvbSIsICJoaXN0b3J5SWQiOiAxMjM0NX0=",
            "messageId": "msg123",
        },
        "subscription": "projects/test/subscriptions/sub1",
    }

    response = client.post(
        "/api/v1/email/new",
        json=payload,
        headers={"X-API-Key": TEST_API_KEY},
    )

    # Note: Logic inside EmailProcessorService might prevent full execution if not mocked deeper,
    # but we just want to ensure the endpoint is wired correctly.
    # If EmailProcessorService fails, we expect 500 or specific error.
    # Since we mocked repo and client, it should proceed.

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_webhook_endpoint_missing_api_key(client):
    """Test POST /api/v1/email/new returns 401 without API key."""
    payload = {
        "message": {
            "data": "eyJlbWFpbEFkZHJlc3MiOiAidGVzdEBleGFtcGxlLmNvbSIsICJoaXN0b3J5SWQiOiAxMjM0NX0=",
            "messageId": "msg123",
        },
        "subscription": "projects/test/subscriptions/sub1",
    }

    response = client.post("/api/v1/email/new", json=payload)

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid authentication"
