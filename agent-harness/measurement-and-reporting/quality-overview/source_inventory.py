import hashlib
import json
import os
from pathlib import Path
import sys


GENERATED_FILES = {
    "plugin.json",
    ".claude-plugin/plugin.json",
    "artifact-inventory.json",
    ".codex-plugin/plugin.json",
    ".codex-plugin/plugin.json.dotagents-managed",
    ".dotagents-managed",
    ".dotagents-native-fallbacks",
}


def _record_source_directory(directory, visited):
    canonical = Path(directory).resolve(strict=True)
    if canonical in visited or len(visited) >= 10000:
        raise ValueError("Source directory cycle or resource limit exceeded")
    visited.add(canonical)


def _walk_source_directory(source):
    visited = set()
    for directory, _, names in os.walk(source, followlinks=True):
        _record_source_directory(directory, visited)
        for name in sorted(names):
            path = Path(directory) / name
            if not path.is_file():
                raise ValueError("Source inventory contains a non-file entry")
            yield path, path.relative_to(source)


def source_files(source):
    if source.is_file():
        yield source, Path()
        return
    yield from _walk_source_directory(source)


def _validate_artifact_paths(artifact):
    destination = Path(artifact["name"])
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("Source destination escapes the package")
    source = Path(artifact["source"])
    if not source.is_absolute():
        raise ValueError("Source inventory must use absolute origins")
    return destination, source


def artifact_files(artifact):
    destination, source = _validate_artifact_paths(artifact)
    count = 0
    for expected, relative in source_files(source):
        count += 1
        yield expected, str(destination / relative)
    if count == 0:
        raise ValueError("Source artifact contains no files")


def _required_file_record(expected, name):
    return {
        "path": f"plugin/{name}",
        "sha256": hashlib.sha256(expected.read_bytes()).hexdigest(),
        "executable": bool(expected.stat().st_mode & 0o111),
    }


def _validate_required_destination(name, required):
    if name in required or name in GENERATED_FILES:
        raise ValueError("Source inventory contains a destination collision")


def _validate_required_limits(required, total_bytes):
    if len(required) >= 10000 or total_bytes > 67108864:
        raise ValueError("Source inventory resource limit exceeded")


def _add_artifact_files(artifact, required, total_bytes):
    for expected, name in artifact_files(artifact):
        _validate_required_destination(name, required)
        total_bytes += expected.stat().st_size
        _validate_required_limits(required, total_bytes)
        required[name] = _required_file_record(expected, name)
    return total_bytes


def required_source_files(package):
    inventory = json.loads((package / "artifact-inventory.json").read_text())
    artifacts = inventory["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Source inventory must contain artifacts")
    required = {}
    total_bytes = 0
    for artifact in artifacts:
        total_bytes = _add_artifact_files(artifact, required, total_bytes)
    return inventory, required, total_bytes


def _verify_required_file(package, name, expected):
    actual = (package / name).resolve(strict=True)
    if not actual.is_relative_to(package):
        raise ValueError("Delivered source escapes the package")
    if hashlib.sha256(actual.read_bytes()).hexdigest() != expected["sha256"]:
        raise ValueError(f"Delivered source bytes differ: {name}")
    if bool(actual.stat().st_mode & 0o111) != expected["executable"]:
        raise ValueError(f"Delivered source executable mode differs: {name}")


def verify_preservation(bundle):
    package = (bundle / "plugin").resolve(strict=True)
    inventory, required, total_bytes = required_source_files(package)
    actual_files = {str(relative) for _, relative in source_files(package)}
    if actual_files != set(required) | GENERATED_FILES:
        raise ValueError("Delivered file inventory differs from sources and metadata")
    for name, expected in required.items():
        _verify_required_file(package, name, expected)
    return {
        "artifacts": len(inventory["artifacts"]),
        "files": len(required),
        "bytes": total_bytes,
        "metadataFiles": len(GENERATED_FILES),
        "requiredFiles": list(required.values()),
    }


if __name__ == "__main__":
    print(json.dumps(verify_preservation(Path(sys.argv[1]))))
