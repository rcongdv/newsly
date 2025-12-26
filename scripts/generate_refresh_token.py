"""
Script to generate a Gmail OAuth refresh token using your own client credentials.

This script will:
1. Open a browser window for you to authorize the app
2. Generate a refresh token
3. Display the token so you can save it to your .env file

Run this script once to get a new refresh token.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Load your OAuth client credentials from .env
CLIENT_ID = os.getenv("GOOGLE_AUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_AUTH_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Missing GOOGLE_AUTH_CLIENT_ID or GOOGLE_AUTH_CLIENT_SECRET in .env")
    exit(1)

# Create the OAuth client configuration
client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080/"],
    }
}

print("=" * 60)
print("Gmail OAuth Refresh Token Generator")
print("=" * 60)
print("\nThis will open a browser window for you to authorize the app.")
print("After authorization, you'll receive a refresh token.\n")

try:
    # Run the OAuth flow
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)

    # This will open a browser window
    creds = flow.run_local_server(port=8080)

    print("\n" + "=" * 60)
    print("SUCCESS! Your refresh token:")
    print("=" * 60)
    print(f"\n{creds.refresh_token}\n")
    print("=" * 60)
    print(
        "\nCopy the token above and update GOOGLE_AUTH_REFRESH_TOKEN in your .env file"
    )
    print("=" * 60)

except Exception as e:
    print(f"\nERROR: Failed to generate refresh token: {e}")
    print("\nTroubleshooting:")
    print(
        "1. Make sure your OAuth client is configured as 'Desktop app' or 'Web application'"
    )
    print(
        "2. Add 'http://localhost:8080' to authorized redirect URIs in Google Cloud Console"
    )
    print("3. Enable the Gmail API in your Google Cloud project")
    exit(1)
