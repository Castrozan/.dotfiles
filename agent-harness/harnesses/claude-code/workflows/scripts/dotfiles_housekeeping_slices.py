import argparse
import json
import math
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

TARGET_LINES_PER_SLICE = 3000
MAXIMUM_SLICES = 12
MAXIMUM_LINES_PER_FILE = 3000


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="dotfiles-housekeeping-slices",
        description="Write numbered slice artifacts of one subtree for the dotfiles-housekeeping workflow.",
    )
    parser.add_argument("--root", required=True, help="absolute checkout path")
    parser.add_argument(
        "--subtree", required=True, help="path inside the checkout to audit"
    )
    return parser.parse_args()


def tracked_files(root, subtree):
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", subtree],
        capture_output=True,
        check=True,
    )
    return [name.decode() for name in listed.stdout.split(b"\0") if name]


def readable_text_lines(path):
    content = path.read_bytes()
    if b"\0" in content:
        return None
    try:
        lines = content.decode().splitlines()
    except UnicodeDecodeError:
        return None
    if len(lines) > MAXIMUM_LINES_PER_FILE:
        return None
    return lines


def subtree_files_with_lines(root, subtree):
    files = []
    for relative_path in tracked_files(root, subtree):
        lines = readable_text_lines(root / relative_path)
        if lines:
            files.append((relative_path, lines))
    return files


def too_large_report(files, subtree, total_lines):
    lines_by_child = Counter()
    for relative_path, lines in files:
        remainder = Path(relative_path).relative_to(subtree).parts
        lines_by_child[str(Path(subtree, remainder[0]))] += len(lines)
    subdirectory_sizes = ", ".join(
        f"{child} ({count} lines)" for child, count in lines_by_child.most_common()
    )
    return {
        "error": (
            f"{subtree} holds {total_lines} lines, more than {MAXIMUM_SLICES} slices of "
            f"{TARGET_LINES_PER_SLICE}; audit one of its subdirectories instead: "
            f"{subdirectory_sizes}"
        )
    }


def numbered_file_section(relative_path, lines):
    numbered = "\n".join(f"{number:5d}  {text}" for number, text in enumerate(lines, 1))
    return f"=== {relative_path} ({len(lines)} lines)\n{numbered}"


def grouped_slice_sections(files, slice_count):
    lines_per_slice = math.ceil(sum(len(lines) for _, lines in files) / slice_count)
    slices, current_sections, current_lines = [], [], 0
    for relative_path, lines in files:
        current_sections.append(numbered_file_section(relative_path, lines))
        current_lines += len(lines)
        if current_lines >= lines_per_slice and len(slices) < slice_count - 1:
            slices.append(current_sections)
            current_sections, current_lines = [], 0
    if current_sections:
        slices.append(current_sections)
    return slices


def write_slice_artifacts(files, slice_count):
    artifact_directory = Path(tempfile.mkdtemp(prefix="dotfiles-housekeeping-"))
    artifact_paths = []
    for slice_index, sections in enumerate(grouped_slice_sections(files, slice_count)):
        artifact_path = artifact_directory / f"slice-{slice_index}.txt"
        artifact_path.write_text("\n\n".join(sections) + "\n")
        artifact_paths.append(str(artifact_path))
    return artifact_paths


def subtree_inside_root(root, requested_subtree):
    requested_path = Path(requested_subtree).expanduser()
    if requested_path.is_absolute():
        requested_path = requested_path.resolve().relative_to(root)
    return str(requested_path).strip("/")


def main():
    arguments = parse_command_line()
    root = Path(arguments.root).expanduser().resolve()
    subtree = subtree_inside_root(root, arguments.subtree)
    files = subtree_files_with_lines(root, subtree)
    total_lines = sum(len(lines) for _, lines in files)
    if not files:
        print(json.dumps({"error": f"{subtree} holds no tracked text files"}))
        return
    slice_count = math.ceil(total_lines / TARGET_LINES_PER_SLICE)
    if slice_count > MAXIMUM_SLICES:
        print(json.dumps(too_large_report(files, subtree, total_lines)))
        return
    print(
        json.dumps(
            {
                "slices": write_slice_artifacts(files, slice_count),
                "files": len(files),
                "lines": total_lines,
            }
        )
    )


if __name__ == "__main__":
    main()
