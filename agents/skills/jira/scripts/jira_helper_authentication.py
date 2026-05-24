import os
import sys
from pathlib import Path

JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME = "JIRA_API_TOKEN"
JIRA_API_TOKEN_SECRET_FILE_PATH = Path.home() / ".secrets" / "jira-api-token"


def load_jira_api_token_into_environment_if_missing():
    if os.environ.get(JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME):
        return
    if not JIRA_API_TOKEN_SECRET_FILE_PATH.is_file():
        print(
            f"Error: {JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME} not set and "
            f"{JIRA_API_TOKEN_SECRET_FILE_PATH} not found. "
            "Run rebuild to deploy agenix secrets.",
            file=sys.stderr,
        )
        sys.exit(1)
    os.environ[JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME] = (
        JIRA_API_TOKEN_SECRET_FILE_PATH.read_text().strip()
    )
