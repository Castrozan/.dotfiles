import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from artifact_selection import ARTIFACT_PRODUCERS
from workflow_context import REPOSITORY


MAXIMUM_ARCHIVE_BYTES = 67108864
MAXIMUM_EXTRACTED_BYTES = 268435456
MAXIMUM_ENTRIES = 10000
UNSAFE_ARCHIVE_ENTRY_MESSAGE = "Artifact contains an unsafe or duplicate path"


def _archive_content_exceeds_limits(entries):
    return (
        len(entries) > MAXIMUM_ENTRIES
        or sum(entry.file_size for entry in entries) > MAXIMUM_EXTRACTED_BYTES
    )


def _archive_path_has_unsafe_location(path, filename, paths):
    return path.is_absolute() or ".." in path.parts or "\\" in filename or path in paths


def _validate_archive_entry(entry, paths):
    path = PurePosixPath(entry.filename)
    mode = entry.external_attr >> 16
    if _archive_path_has_unsafe_location(path, entry.filename, paths):
        raise ValueError(UNSAFE_ARCHIVE_ENTRY_MESSAGE)
    if stat.S_ISLNK(mode):
        raise ValueError(UNSAFE_ARCHIVE_ENTRY_MESSAGE)
    if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise ValueError(UNSAFE_ARCHIVE_ENTRY_MESSAGE)
    if not path.parts:
        raise ValueError(UNSAFE_ARCHIVE_ENTRY_MESSAGE)
    return path


def extract_archive(archive, destination, expected_digest):
    if archive.stat().st_size > MAXIMUM_ARCHIVE_BYTES:
        raise ValueError("Artifact archive exceeds the download limit")
    with archive.open("rb") as stream:
        actual_digest = sha256(stream.read()).hexdigest()
    if expected_digest != f"sha256:{actual_digest}":
        raise ValueError("Artifact archive digest differs from GitHub metadata")
    with ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if _archive_content_exceeds_limits(entries):
            raise ValueError("Artifact contents exceed extraction limits")
        paths = set()
        for entry in entries:
            path = _validate_archive_entry(entry, paths)
            paths.add(path)
        bundle.extractall(destination)


def download_artifact(selection, destination):
    identifier = selection["id"]
    if type(identifier) is not int or identifier < 1:
        raise ValueError("Artifact identifier must be positive")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", selection.get("digest", "")):
        raise ValueError("Artifact digest is unavailable")
    with TemporaryDirectory(
        prefix="quality-artifact-", dir=destination.parent
    ) as temporary:
        root = Path(temporary)
        archive = root / "artifact.zip"
        with archive.open("wb") as output:
            subprocess.run(
                [
                    "gh",
                    "api",
                    "--method",
                    "GET",
                    "--",
                    f"repos/{REPOSITORY}/actions/artifacts/{identifier}/zip",
                ],
                stdout=output,
                stderr=subprocess.PIPE,
                timeout=60,
                check=True,
            )
        extracted = root / "extracted"
        extract_archive(archive, extracted, selection["digest"])
        if destination.exists():
            raise ValueError("Artifact destination already exists")
        extracted.rename(destination)


def download_selected(context, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_PRODUCERS:
        selection = context["artifacts"][name]
        if not selection["id"]:
            continue
        try:
            download_artifact(selection, destination / name)
        except (OSError, ValueError, BadZipFile, subprocess.SubprocessError) as error:
            context["artifacts"][name] = {
                **selection,
                "id": None,
                "reason": f"Selected artifact {selection['id']} could not be downloaded: {type(error).__name__}: {error}",
            }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("context", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    context = json.loads(arguments.context.read_text())
    download_selected(context, arguments.destination)
    arguments.context.write_text(json.dumps(context, indent=2) + "\n")


if __name__ == "__main__":
    main()
