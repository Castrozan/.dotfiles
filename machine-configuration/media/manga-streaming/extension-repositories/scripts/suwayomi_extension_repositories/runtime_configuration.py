import json
import os
import sys
from pathlib import Path

DECLARED_REPOSITORY_LIST_FILE_VARIABLE = "SUWAYOMI_EXTENSION_REPOSITORIES_FILE"
GRAPHQL_URL_VARIABLE = "SUWAYOMI_GRAPHQL_URL"
SUWAYOMI_ACCEPTED_REPOSITORY_URL_PREFIX = "https://raw.githubusercontent.com/"


def graphql_url() -> str:
    declared_url = os.environ.get(GRAPHQL_URL_VARIABLE, "").strip()
    if not declared_url:
        print(f"{GRAPHQL_URL_VARIABLE} is unset", file=sys.stderr)
        raise SystemExit(1)
    return declared_url


def declared_repository_list_file() -> Path:
    declared_path = os.environ.get(DECLARED_REPOSITORY_LIST_FILE_VARIABLE, "").strip()
    if not declared_path:
        print(f"{DECLARED_REPOSITORY_LIST_FILE_VARIABLE} is unset", file=sys.stderr)
        raise SystemExit(1)
    return Path(declared_path)


def declared_repository_urls():
    list_file_path = declared_repository_list_file()
    if not list_file_path.is_file():
        return None
    repository_urls = [
        entry.strip()
        for entry in json.loads(list_file_path.read_text(encoding="utf-8"))
        if entry.strip()
    ]
    if not repository_urls:
        print(
            f"{list_file_path} declares no repository, which would leave Suwayomi "
            "unable to install any extension",
            file=sys.stderr,
        )
        raise SystemExit(1)
    unacceptable_repository_urls = [
        repository_url
        for repository_url in repository_urls
        if not repository_url.startswith(SUWAYOMI_ACCEPTED_REPOSITORY_URL_PREFIX)
    ]
    if unacceptable_repository_urls:
        print(
            "Suwayomi only accepts a repository served from "
            f"{SUWAYOMI_ACCEPTED_REPOSITORY_URL_PREFIX} and rejects the whole list "
            "when one entry is elsewhere, so these would take every other "
            f"repository down with them: {', '.join(unacceptable_repository_urls)}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return repository_urls
