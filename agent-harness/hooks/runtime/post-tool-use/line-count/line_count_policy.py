"""Shared policy for file-length limits enforced by hook and CI scanner."""

from __future__ import annotations

import os
from dataclasses import dataclass

LINE_COUNT_BLOCKING_THRESHOLD = 200

CODE_FILE_EXTENSIONS = frozenset(
    {
        ".py",
        ".pyi",
        ".pyx",
        ".nix",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".go",
        ".rs",
        ".rb",
        ".java",
        ".kt",
        ".kts",
        ".scala",
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".h",
        ".hh",
        ".hpp",
        ".hxx",
        ".m",
        ".mm",
        ".swift",
        ".lua",
        ".vim",
        ".ex",
        ".exs",
        ".erl",
        ".ml",
        ".mli",
        ".clj",
        ".cljs",
        ".cljc",
        ".hs",
        ".pl",
        ".pm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".qml",
        ".sql",
        ".tf",
        ".tfvars",
        ".dart",
        ".jl",
        ".r",
        ".php",
        ".graphql",
        ".gql",
        ".proto",
    }
)


@dataclass(frozen=True)
class LineCountViolation:
    file_path: str
    line_count: int
    allowed_line_count: int


def file_path_has_code_extension(file_path: str) -> bool:
    _root, extension = os.path.splitext(file_path)
    return extension.lower() in CODE_FILE_EXTENSIONS


def count_lines_in_file(file_path: str) -> int:
    with open(file_path, "rb") as binary_file_handle:
        contents = binary_file_handle.read()
    if not contents:
        return 0
    line_count = contents.count(b"\n")
    if not contents.endswith(b"\n"):
        line_count += 1
    return line_count


def code_file_line_count(file_path: str) -> int | None:
    if not file_path_has_code_extension(file_path):
        return None
    if not os.path.isfile(file_path):
        return None
    try:
        return count_lines_in_file(file_path)
    except OSError:
        return None


def line_count_violation(
    file_path: str, allowed_line_count: int
) -> LineCountViolation | None:
    line_count = code_file_line_count(file_path)
    if line_count is None or line_count <= allowed_line_count:
        return None
    return LineCountViolation(file_path, line_count, allowed_line_count)
