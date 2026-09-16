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

    credentials = None
    token_path = Path(TOKEN_PATH)

    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            credentials_path = Path(CREDENTIALS_PATH)
            if not credentials_path.exists():
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

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json())

    return build("youtube", "v3", credentials=credentials)
