import json
import os
from pathlib import PurePosixPath

from jellyseerr_media import JellyseerrMedia
from media_library import PUBLIC_LIBRARY_DIRECTORIES, load_media_library


class MediaRemovalDenied(ValueError):
    pass


def authorize_media_removal():
    operator = os.environ.get("ARR_MEDIA_OPERATOR_DISCORD_USER_ID")
    try:
        envelope = json.loads(os.environ.get("CLAWDE_CHANNEL_PROMPT", ""))
    except ValueError:
        envelope = None
    if not isinstance(envelope, dict):
        raise MediaRemovalDenied("Media removal requires the verified Discord operator")
    if not operator or (envelope.get("source"), envelope.get("user_id")) != (
        "discord",
        operator,
    ):
        raise MediaRemovalDenied("Media removal requires the verified Discord operator")


def validate_native_media_identity(details, media_type):
    media = details["mediaInfo"]
    if (media.get("tmdbId"), media.get("mediaType")) != (details["id"], media_type):
        raise ValueError("Removal target identity is inconsistent")
    if media_type == "movie" and str(media.get("externalServiceSlug")) != str(
        details["id"]
    ):
        raise ValueError("Removal target identity is inconsistent")


def validate_arr_library_identity(record, details, media_type, external_identifier):
    identity_field, identity = (
        ("tmdbId", details["id"])
        if media_type == "movie"
        else ("tvdbId", (details.get("externalIds") or {}).get("tvdbId"))
    )
    if not identity or (record.get("id"), record.get(identity_field)) != (
        external_identifier,
        identity,
    ):
        raise ValueError("Removal target is not the identified public library item")


def validate_public_library_path(record, media_type):
    path = PurePosixPath(record.get("path", ""))
    if (
        path.parent != PurePosixPath(PUBLIC_LIBRARY_DIRECTORIES[media_type])
        or ".." in path.parts
    ):
        raise ValueError("Removal target is outside the public library")


def validate_public_library_item(record, details, media_type, external_identifier):
    validate_native_media_identity(details, media_type)
    validate_arr_library_identity(record, details, media_type, external_identifier)
    validate_public_library_path(record, media_type)


def remove_media(client, stack_home, media_type, media_id):
    details = client.details(media_type, media_id)
    media = details.get("mediaInfo") or {}
    result = {"media_type": media_type, "media_id": media_id}
    external_identifier = media.get("externalServiceId")
    if not external_identifier:
        return {"result": "not_present", "library_files": "unchanged", **result}
    library = load_media_library(stack_home, media_type, media.get("serviceId"))
    record = library.item(external_identifier)
    if record is None:
        return {"result": "not_present", "library_files": "unchanged", **result}
    validate_public_library_item(record, details, media_type, external_identifier)
    administrator = JellyseerrMedia(client.api_key)
    administrator.request("DELETE", f"/media/{media['id']}/file?is4k=false")
    if library.item(external_identifier) is not None:
        raise ValueError("Media removal is unconfirmed")
    return {"result": "media_removed", "library_files": "deletion_requested", **result}
