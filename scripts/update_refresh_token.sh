#!/usr/bin/env bash
source venv/bin/activate

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
ENV_FILE="${SCRIPT_DIR}/../.env"

echo "Running generate_refresh_token.py..."
OUTPUT="$(python "${SCRIPT_DIR}/generate_refresh_token.py")"

# Extract token: non-empty line after "SUCCESS!" header and its separator
TOKEN="$(echo "$OUTPUT" | awk '/^SUCCESS/{found=1} found && !/^=/ && !/^SUCCESS/ && /./{print; exit}' | tr -d '[:space:]')"

if [ -z "$TOKEN" ]; then
    echo "Error: Could not extract refresh token from script output" >&2
    echo "$OUTPUT" >&2
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE" >&2
    exit 1
fi

if grep -q '^GOOGLE_AUTH_REFRESH_TOKEN=' "$ENV_FILE"; then
    sed -i '' "s|^GOOGLE_AUTH_REFRESH_TOKEN=.*|GOOGLE_AUTH_REFRESH_TOKEN=\"${TOKEN}\"|" "$ENV_FILE"
else
    echo "GOOGLE_AUTH_REFRESH_TOKEN=\"${TOKEN}\"" >> "$ENV_FILE"
fi

echo "Updated GOOGLE_AUTH_REFRESH_TOKEN in $ENV_FILE"

fly deploy
