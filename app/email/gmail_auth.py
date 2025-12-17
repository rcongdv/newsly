import dotenv
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError


dotenv.load_dotenv()


class GmailAuth:

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_AUTH_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_AUTH_CLIENT_SECRET")
        self.refresh_token = os.getenv("GOOGLE_AUTH_REFRESH_TOKEN")

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError(
                "Missing required GOOGLE_ environment variables. Cannot initialize GoogleAuthService."
            )

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
