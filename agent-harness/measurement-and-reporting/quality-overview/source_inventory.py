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


def source_files(source):
    if source.is_file():
        yield source, Path()
        return
    visited = set()
    for directory, _, names in os.walk(source, followlinks=True):
        canonical = Path(directory).resolve(strict=True)
        if canonical in visited or len(visited) >= 10000:
            raise ValueError("Source directory cycle or resource limit exceeded")
        visited.add(canonical)
        for name in sorted(names):
            path = Path(directory) / name
            if not path.is_file():
                raise ValueError("Source inventory contains a non-file entry")
            yield path, path.relative_to(source)


def artifact_files(artifact):
    destination = Path(artifact["name"])
    if destination.is_absolute() or ".." in destination.parts:
        raise ValueError("Source destination escapes the package")
    source = Path(artifact["source"])
    if not source.is_absolute():
        raise ValueError("Source inventory must use absolute origins")
    count = 0
    for expected, relative in source_files(source):
        count += 1
        yield expected, str(destination / relative)
    if count == 0:
        raise ValueError("Source artifact contains no files")


def required_source_files(package):
    inventory = json.loads((package / "artifact-inventory.json").read_text())
    artifacts = inventory["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Source inventory must contain artifacts")
    required = {}
    total_bytes = 0
    for artifact in artifacts:
        for expected, name in artifact_files(artifact):
            if name in required or name in GENERATED_FILES:
                raise ValueError("Source inventory contains a destination collision")
            total_bytes += expected.stat().st_size
            if len(required) >= 10000 or total_bytes > 67108864:
                raise ValueError("Source inventory resource limit exceeded")
            required[name] = {
                "path": f"plugin/{name}",
                "sha256": hashlib.sha256(expected.read_bytes()).hexdigest(),
                "executable": bool(expected.stat().st_mode & 0o111),
            }
    return inventory, required, total_bytes


def verify_preservation(bundle):
    package = (bundle / "plugin").resolve(strict=True)
    inventory, required, total_bytes = required_source_files(package)
    actual_files = {str(relative) for _, relative in source_files(package)}
    if actual_files != set(required) | GENERATED_FILES:
        raise ValueError("Delivered file inventory differs from sources and metadata")
    for name, expected in required.items():
        actual = (package / name).resolve(strict=True)
        if not actual.is_relative_to(package):
            raise ValueError("Delivered source escapes the package")
        if hashlib.sha256(actual.read_bytes()).hexdigest() != expected["sha256"]:
            raise ValueError(f"Delivered source bytes differ: {name}")
        if bool(actual.stat().st_mode & 0o111) != expected["executable"]:
            raise ValueError(f"Delivered source executable mode differs: {name}")
    return {
        "artifacts": len(inventory["artifacts"]),
        "files": len(required),
        "bytes": total_bytes,
        "metadataFiles": len(GENERATED_FILES),
        "requiredFiles": list(required.values()),
    }


if __name__ == "__main__":
    print(json.dumps(verify_preservation(Path(sys.argv[1]))))
