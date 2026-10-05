import hashlib
import os
from dataclasses import asdict
from pathlib import Path

from media_video.contract import PreparedRecipe, VideoError
from media_video.files import (
    canonical_json,
    create_private_directory,
    file_digest,
    regular_file,
    retained_file,
    sync_directory,
)


def request_digest(request, recipe, renderer):
    identity = {
        "request": asdict(request),
        "renderer": renderer.name,
        "adapter_version": renderer.adapter_version,
        "renderer_version": recipe.renderer_version,
        "registration_sha256": recipe.registration.sha256,
        "manifest_sha256": recipe.manifest.sha256,
        "binary_sha256": recipe.binary.sha256,
        "files": [
            {"path": item.relative_path, "sha256": item.sha256} for item in recipe.files
        ],
    }
    return hashlib.sha256(canonical_json(identity)).hexdigest()


def copy_registered_file(registered, destination, deadline):
    regular_file(registered.source_path)
    create_private_directory(destination.parent)
    input_descriptor = os.open(registered.source_path, os.O_RDONLY | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    with os.fdopen(input_descriptor, "rb") as input_file:
        output_descriptor = os.open(
            destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        with os.fdopen(output_descriptor, "wb") as output_file:
            while chunk := input_file.read(1024 * 1024):
                deadline.remaining()
                digest.update(chunk)
                output_file.write(chunk)
            output_file.flush()
            os.fsync(output_file.fileno())
    if digest.hexdigest() != registered.sha256:
        raise VideoError("registered_input_changed")
    deadline.remaining()


def preserve_inputs(recipe, directory, deadline):
    input_directory = directory / "inputs"
    recipe_directory = input_directory / "recipe"
    create_private_directory(recipe_directory)
    entries = [
        (recipe.registration, input_directory / "registration.json"),
        (recipe.manifest, input_directory / "source-assets-manifest.json"),
        (recipe.binary, input_directory / "renderer"),
        *((entry, recipe_directory / entry.relative_path) for entry in recipe.files),
    ]
    retained = []
    for registered, destination in entries:
        copy_registered_file(registered, destination, deadline)
        retained.append(retained_file(destination, directory, deadline))
    os.chmod(input_directory / "renderer", 0o700)
    directories = {directory}
    for _, entry in entries:
        directories.update(
            parent for parent in entry.parents if parent.is_relative_to(directory)
        )
    for nested in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        sync_directory(nested)
    return PreparedRecipe(input_directory / "renderer", recipe_directory), retained


def verify_retained_inputs(directory, retained, deadline=None):
    if not isinstance(retained, list) or not 4 <= len(retained) <= 515:
        raise VideoError("invalid_receipt")
    for entry in retained:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise VideoError("invalid_receipt")
        relative = Path(entry["path"])
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not relative.is_relative_to("inputs")
            or str(relative) != entry["path"]
        ):
            raise VideoError("invalid_receipt")
        path = directory / relative
        try:
            digest = file_digest(path, deadline)
        except FileNotFoundError:
            raise VideoError("input_unavailable") from None
        if digest != entry.get("sha256"):
            raise VideoError("input_checksum_mismatch")
