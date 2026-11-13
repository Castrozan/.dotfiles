import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from ingestion_snapshot_publisher import IngestionRefusedError

MAXIMUM_ARTIFACT_BYTE_LENGTH = 4_000_000
MAXIMUM_ARTIFACT_KEY_CODE_UNITS = 512
PREFLIGHT_READ_BYTE_LENGTH = 65536
MAXIMUM_REPORT_TREE_FILE_COUNT = 1024
MAXIMUM_REPORT_TREE_BYTE_LENGTH = 32_000_000
MAXIMUM_REPORT_TREE_ENTRY_COUNT = 4096


@dataclass(frozen=True)
class ArtifactSource:
    relative_path: str
    file_path: Path
    byte_length: int
    sha256: str


@dataclass
class ArtifactTreeBudget:
    entry_count: int = 0
    file_count: int = 0
    byte_length: int = 0

    def record_entry(self):
        self.entry_count += 1
        if self.entry_count > MAXIMUM_REPORT_TREE_ENTRY_COUNT:
            raise IngestionRefusedError("Report artifact tree exceeds the entry limit")

    def record_file(self):
        self.file_count += 1
        if self.file_count > MAXIMUM_REPORT_TREE_FILE_COUNT:
            raise IngestionRefusedError("Report artifact tree exceeds the file limit")

    def record_bytes(self, chunk_byte_length):
        self.byte_length += chunk_byte_length
        if self.byte_length > MAXIMUM_REPORT_TREE_BYTE_LENGTH:
            raise IngestionRefusedError("Report artifact tree exceeds the byte limit")


def is_forbidden_key_character(character):
    return ord(character) < 32 or ord(character) == 127 or character == "\\"


def require_publishable_name(relative_path, object_key_prefix):
    try:
        relative_path.encode("utf-8")
        object_key_units = (
            len(f"{object_key_prefix}{relative_path}".encode("utf-16-le")) // 2
        )
    except UnicodeError as name_failure:
        raise IngestionRefusedError(
            "Report artifact name is not UTF-8"
        ) from name_failure
    if any(is_forbidden_key_character(character) for character in relative_path):
        raise IngestionRefusedError(
            "Report artifact name contains forbidden characters"
        )
    if object_key_units > MAXIMUM_ARTIFACT_KEY_CODE_UNITS:
        raise IngestionRefusedError("Report artifact key exceeds the worker limit")


def require_within_request_limit(relative_path, byte_length):
    if byte_length > MAXIMUM_ARTIFACT_BYTE_LENGTH:
        raise IngestionRefusedError(
            f"Report artifact exceeds the request limit: {relative_path!r}"
        )


def capture_artifact_source(file_path, relative_path, budget):
    require_within_request_limit(relative_path, file_path.stat().st_size)
    budget.record_file()
    digest = hashlib.sha256()
    byte_length = 0
    with file_path.open("rb") as body_stream:
        for chunk in iter(lambda: body_stream.read(PREFLIGHT_READ_BYTE_LENGTH), b""):
            byte_length += len(chunk)
            require_within_request_limit(relative_path, byte_length)
            budget.record_bytes(len(chunk))
            digest.update(chunk)
    return ArtifactSource(relative_path, file_path, byte_length, digest.hexdigest())


def inspect_artifact_entry(entry, relative_path, object_key_prefix, budget):
    require_publishable_name(relative_path, object_key_prefix)
    if entry.is_symlink():
        raise IngestionRefusedError(
            f"Report artifact symlink refused: {relative_path!r}"
        )
    if entry.is_dir(follow_symlinks=False):
        return None
    if not entry.is_file(follow_symlinks=False):
        raise IngestionRefusedError(
            f"Report artifact special entry refused: {relative_path!r}"
        )
    return capture_artifact_source(Path(entry.path), relative_path, budget)


@dataclass(frozen=True)
class ArtifactDirectoryContents:
    sources: list[ArtifactSource]
    directories: list[tuple[Path, str]]


def scan_artifact_directory(directory, relative_directory, object_key_prefix, budget):
    sources = []
    directories = []
    with os.scandir(directory) as entries:
        for entry in entries:
            budget.record_entry()
            relative_path = f"{relative_directory}{entry.name}"
            source = inspect_artifact_entry(
                entry, relative_path, object_key_prefix, budget
            )
            if source is None:
                directories.append((Path(entry.path), f"{relative_path}/"))
            else:
                sources.append(source)
    return ArtifactDirectoryContents(sources, directories)


def collect_artifact_sources(directory, object_key_prefix):
    if directory.is_symlink() or not directory.is_dir():
        raise IngestionRefusedError("Report artifact source must be a real directory")
    sources = []
    budget = ArtifactTreeBudget()
    pending_directories = [(directory, "")]
    while pending_directories:
        current_directory, relative_directory = pending_directories.pop()
        contents = scan_artifact_directory(
            current_directory, relative_directory, object_key_prefix, budget
        )
        sources.extend(contents.sources)
        pending_directories.extend(contents.directories)
    if not sources:
        raise IngestionRefusedError("Report artifact tree has no files to publish")
    return sources
