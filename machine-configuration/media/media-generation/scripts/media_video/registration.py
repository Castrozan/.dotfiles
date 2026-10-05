import os
import re
from pathlib import Path, PurePosixPath

from media_video.contract import RegisteredFile, RegisteredRecipe, VideoError
from media_video.files import file_digest, private_directory, read_json, valid_digest


def pinned_file(value, relative_path, deadline):
    if (
        not isinstance(value, dict)
        or set(value) != {"path", "sha256"}
        or not isinstance(value["path"], str)
        or "\x00" in value["path"]
        or not valid_digest(value["sha256"])
    ):
        raise VideoError("invalid_registration")
    path = Path(value["path"])
    actual_digest = file_digest(path, deadline)
    if actual_digest != value["sha256"]:
        raise VideoError("registered_input_changed")
    return RegisteredFile(path, relative_path, actual_digest)


def load_recipe_registration(path, deadline):
    registration_digest = file_digest(path, deadline)
    document = read_json(path, private=True)
    if set(document) != {
        "recipe_id",
        "recipe_directory",
        "renderer_version",
        "binary",
        "source_assets_manifest",
    }:
        raise VideoError("invalid_registration")
    if not isinstance(document["recipe_id"], str) or not re.fullmatch(
        "[a-zA-Z0-9_-]{1,100}", document["recipe_id"]
    ):
        raise VideoError("invalid_registration")
    if (
        not isinstance(document["renderer_version"], str)
        or not document["renderer_version"].strip()
        or len(document["renderer_version"]) > 200
        or not isinstance(document["recipe_directory"], str)
        or "\x00" in document["recipe_directory"]
    ):
        raise VideoError("invalid_registration")
    recipe_directory = Path(document["recipe_directory"])
    private_directory(recipe_directory)
    manifest = pinned_file(
        document["source_assets_manifest"], "manifest.json", deadline
    )
    manifest_document = read_json(manifest.source_path, private=True)
    if file_digest(manifest.source_path, deadline) != manifest.sha256:
        raise VideoError("registered_input_changed")
    if set(manifest_document) != {"files"}:
        raise VideoError("invalid_manifest")
    entries = manifest_document["files"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 512:
        raise VideoError("invalid_manifest")
    binary = pinned_file(document["binary"], "renderer", deadline)
    if not os.access(binary.source_path, os.X_OK):
        raise VideoError("binary_not_executable")
    with binary.source_path.open("rb") as input_file:
        signature = input_file.read(4)
    if signature not in {
        b"\x7fELF",
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
        b"\xca\xfe\xba\xbf",
        b"\xbf\xba\xfe\xca",
    }:
        raise VideoError("native_binary_required")
    files = []
    seen_paths = set()
    total_bytes = (
        binary.source_path.stat().st_size + manifest.source_path.stat().st_size
    )
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("path"), str)
            or "\x00" in entry["path"]
        ):
            raise VideoError("invalid_manifest")
        relative = PurePosixPath(entry["path"])
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not relative.parts
            or str(relative) != entry["path"]
            or str(relative) in seen_paths
        ):
            raise VideoError("invalid_manifest_path")
        seen_paths.add(str(relative))
        total_bytes += (recipe_directory / str(relative)).stat().st_size
        if total_bytes > 2 * 1024**3:
            raise VideoError("input_too_large")
        registered = pinned_file(
            {**entry, "path": str(recipe_directory / str(relative))},
            str(relative),
            deadline,
        )
        files.append(registered)
    if any(
        first != second and PurePosixPath(first) in PurePosixPath(second).parents
        for first in seen_paths
        for second in seen_paths
    ):
        raise VideoError("invalid_manifest_path")
    deadline.remaining()
    if file_digest(path, deadline) != registration_digest:
        raise VideoError("registered_input_changed")
    return RegisteredRecipe(
        document["recipe_id"],
        recipe_directory,
        document["renderer_version"],
        RegisteredFile(path, "registration.json", registration_digest),
        manifest,
        binary,
        tuple(sorted(files, key=lambda item: item.relative_path)),
    )
