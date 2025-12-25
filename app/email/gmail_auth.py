from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from app.config import get_settings


class GmailAuth:

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.google_auth_client_id
        self.client_secret = settings.google_auth_client_secret
        self.refresh_token = settings.google_auth_refresh_token

        self._credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ],
        )

    def get_credentials(self) -> Credentials:
        if self._credentials.expired or self._credentials.token is None:
            print("Access token expired or missing. Attempting refresh...")
            try:
                self._credentials.refresh(Request())
                print("Token refreshed successfully.")
            except RefreshError as e:
                print(f"FATAL ERROR: Failed to refresh token: {e}")
                raise PermissionError(
                    "Refresh token is invalid or revoked. Requires re-authorization."
                ) from e
            except Exception as e:
                print(f"Unexpected error during refresh: {e}")
                raise RuntimeError(f"Could not get Google credentials: {e}") from e

        return self._credentials

    def get_access_token(self) -> str:
        creds = self.get_credentials()
        if not creds.token:
            raise RuntimeError("Failed to obtain access token.")
        return creds.token
