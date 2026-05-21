"""Shared policy for file-length limits enforced by hook and CI scanner."""

from __future__ import annotations

import os

LINE_COUNT_ADVISORY_THRESHOLD = 100
LINE_COUNT_WARNING_THRESHOLD = 150
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
