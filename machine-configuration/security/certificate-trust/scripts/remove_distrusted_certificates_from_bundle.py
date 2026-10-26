import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CERTIFICATE_ENTRY_MARKER = "=== "
ORGANIZATION_HEADER_MARKER = "### "


@dataclass(frozen=True)
class BundleSegment:
    lines: list[str]

    @property
    def distinguished_name(self) -> str | None:
        first_line = self.lines[0]
        if not first_line.startswith(CERTIFICATE_ENTRY_MARKER):
            return None
        return first_line[len(CERTIFICATE_ENTRY_MARKER) :].rstrip("\n")

    def is_issued_to_any(self, distrusted_common_names: set[str]) -> bool:
        distinguished_name = self.distinguished_name
        if distinguished_name is None:
            return False
        return any(
            distinguished_name.endswith(f"/CN={common_name}")
            for common_name in distrusted_common_names
        )


def split_bundle_into_segments(bundle_text: str) -> list[BundleSegment]:
    segments: list[list[str]] = [[]]
    for line in bundle_text.splitlines(keepends=True):
        starts_new_segment = line.startswith(
            (CERTIFICATE_ENTRY_MARKER, ORGANIZATION_HEADER_MARKER)
        )
        if starts_new_segment and segments[-1]:
            segments.append([])
        segments[-1].append(line)
    return [BundleSegment(lines) for lines in segments if lines]


def remove_distrusted_segments(
    bundle_text: str, distrusted_common_names: set[str]
) -> tuple[str, list[str]]:
    kept_lines: list[str] = []
    removed_distinguished_names: list[str] = []
    for segment in split_bundle_into_segments(bundle_text):
        if segment.is_issued_to_any(distrusted_common_names):
            removed_distinguished_names.append(segment.distinguished_name)
            continue
        kept_lines.extend(segment.lines)
    return "".join(kept_lines), removed_distinguished_names


def replace_file_atomically(path: Path, content: str) -> None:
    original_mode = path.stat().st_mode
    file_descriptor, temporary_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    try:
        with os.fdopen(file_descriptor, "w") as temporary_file:
            temporary_file.write(content)
        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)
    except BaseException:
        Path(temporary_path).unlink(missing_ok=True)
        raise


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Drop certificate entries issued to distrusted authorities from a LibreSSL-style PEM bundle."
    )
    parser.add_argument("--bundle-path", type=Path, required=True)
    parser.add_argument("--distrusted-common-name", action="append", required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    bundle_path: Path = arguments.bundle_path
    if not bundle_path.is_file():
        print(
            f"certificate bundle {bundle_path} is absent, nothing to filter",
            file=sys.stderr,
        )
        return 0
    filtered_text, removed_distinguished_names = remove_distrusted_segments(
        bundle_path.read_text(), set(arguments.distrusted_common_name)
    )
    if not removed_distinguished_names:
        return 0
    replace_file_atomically(bundle_path, filtered_text)
    for distinguished_name in removed_distinguished_names:
        print(
            f"removed distrusted certificate from {bundle_path}: {distinguished_name}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
