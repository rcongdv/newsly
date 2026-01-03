"""Gmail OAuth2 authentication management."""

import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from app.core.exceptions import GmailServiceError

logger = logging.getLogger(__name__)


class GmailAuth:
    """Manages Gmail OAuth2 credentials."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token

        self._credentials = Credentials(
            token=None,
            refresh_token=self._refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=self.SCOPES,
        )

    def get_credentials(self) -> Credentials:
        """Get valid credentials, refreshing if necessary."""
        if self._credentials.expired or self._credentials.token is None:
            logger.info("Access token expired or missing. Attempting refresh...")
            try:
                self._credentials.refresh(Request())
                logger.info("Token refreshed successfully.")
            except RefreshError as e:
                logger.error(f"Failed to refresh token: {e}")
                raise GmailServiceError(
                    "Refresh token is invalid or revoked. Requires re-authorization.",
                    detail=str(e),
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error during refresh: {e}")
                raise GmailServiceError(
                    "Could not get Google credentials",
                    detail=str(e),
                ) from e

        return self._credentials

    def get_access_token(self) -> str:
        """Get the current access token."""
        creds = self.get_credentials()
        if not creds.token:
            raise GmailServiceError("Failed to obtain access token")
        return creds.token
