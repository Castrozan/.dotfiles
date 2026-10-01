"""Audiobookshelf bootstrap: admin login, library ownership, API key issuance."""

import os

from api_client import ApiError, Client
from constants import AUDIOBOOK_LIBRARY_PATH

LIBRARIES_ENDPOINT = "/api/libraries"


def provision_abs(client, credentials, token_file):
    if not client.ready("/status")["isInit"]:
        client.call("/init", {"newRoot": credentials})
    login = client.call("/login", credentials)["user"]
    client.authorize(login.get("accessToken") or login["token"])
    libraries = client.call(LIBRARIES_ENDPOINT)["libraries"]
    matches = [
        library
        for library in libraries
        if any(
            folder.get("fullPath", folder.get("path")) == AUDIOBOOK_LIBRARY_PATH
            for folder in library["folders"]
        )
    ]
    if len(matches) > 1:
        raise RuntimeError(f"Multiple libraries own {AUDIOBOOK_LIBRARY_PATH}")
    library = (
        matches[0]
        if matches
        else client.call(
            LIBRARIES_ENDPOINT,
            {
                "name": "Audiobooks",
                "folders": [{"fullPath": AUDIOBOOK_LIBRARY_PATH}],
                "mediaType": "book",
                "icon": "audiobooks",
            },
        )
    )
    token = token_file.read_text().strip() if token_file.exists() else None
    if token:
        check = Client(client.base, {"Authorization": f"Bearer {token}"})
        try:
            check.call(LIBRARIES_ENDPOINT)
        except ApiError as error:
            if error.status not in (401, 403):
                raise
            token = None
    if not token:
        key = client.call(
            "/api/api-keys",
            {
                "name": "ReadMeABook (Nix managed)",
                "userId": login["id"],
                "isActive": True,
            },
        )
        token = key["apiKey"]["apiKey"]
        temporary = token_file.with_suffix(".tmp")
        with open(
            temporary, "w", opener=lambda path, flags: os.open(path, flags, 0o600)
        ) as stream:
            stream.write(token)
        temporary.replace(token_file)
    return library["id"], token
