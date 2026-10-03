import json
import os
import sys
from pathlib import Path

CREDENTIALS_PATH = os.environ.get(
    "YOUTUBE_CLI_CREDENTIALS",
    str(Path.home() / ".config" / "youtube-cli" / "credentials.json"),
)
TOKEN_PATH = os.environ.get(
    "YOUTUBE_CLI_TOKEN", str(Path.home() / ".config" / "youtube-cli" / "token.json")
)
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def get_authenticated_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_path = Path(TOKEN_PATH)
    credentials = _load_token_credentials(token_path, Credentials)
    if not credentials or not credentials.valid:
        credentials = _authorize_credentials(credentials, Request, InstalledAppFlow)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json())

    return build("youtube", "v3", credentials=credentials)


def _load_token_credentials(token_path, credentials_type):
    if not token_path.exists():
        return None
    return credentials_type.from_authorized_user_file(str(token_path), SCOPES)


def _authorize_credentials(credentials, request_type, flow_type):
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(request_type())
        return credentials
    credentials_path = Path(CREDENTIALS_PATH)
    if not credentials_path.exists():
        _exit_missing_credentials()
    flow = flow_type.from_client_secrets_file(str(credentials_path), SCOPES)
    return flow.run_local_server(port=0)


def _exit_missing_credentials():
    print(
        json.dumps(
            {
                "error": "missing_credentials",
                "message": f"OAuth credentials not found at {CREDENTIALS_PATH}. "
                "Download client_secret.json from Google Cloud Console "
                "(APIs & Services > Credentials > OAuth 2.0 Client IDs) "
                "and save it there.",
            }
        ),
        file=sys.stderr,
    )
    sys.exit(1)
