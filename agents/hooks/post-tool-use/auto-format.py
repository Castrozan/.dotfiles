#!/usr/bin/env python3

import json
import os
import subprocess
import sys

FORMATTERS = {
    ".nix": {
        "formatters": [
            {"cmd": ["nixfmt"], "name": "nixfmt"},
        ],
        "timeout": 10,
    },
    ".py": {
        "formatters": [
            {"cmd": ["ruff", "format", "--quiet"], "name": "ruff"},
        ],
        "timeout": 10,
    },
    ".js": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".ts": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".tsx": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".jsx": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".json": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
            {"cmd": ["jq", ".", "--indent", "2"], "name": "jq", "redirect": True},
        ],
        "timeout": 5,
    },
    ".yaml": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 5,
    },
    ".yml": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 5,
    },
    ".sh": {
        "formatters": [
            {"cmd": ["shfmt", "-w"], "name": "shfmt"},
        ],
        "timeout": 5,
    },
    ".bash": {
        "formatters": [
            {"cmd": ["shfmt", "-w"], "name": "shfmt"},
        ],
        "timeout": 5,
    },
}


def check_formatter_available(formatter_cmd: list[str]) -> bool:
    try:
        subprocess.run([formatter_cmd[0], "--version"], capture_output=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run([formatter_cmd[0], "--help"], capture_output=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def run_formatter(file_path: str, formatter: dict) -> bool:
    cmd = formatter["cmd"] + [file_path]

    try:
        if formatter.get("redirect"):
            with open(file_path, "r") as f:
                content = f.read()

            result = subprocess.run(
                formatter["cmd"],
                input=content,
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                with open(file_path, "w") as f:
                    f.write(result.stdout)
                return True
            return False
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0

    except (subprocess.TimeoutExpired, Exception):
        return False


def find_file_in_ancestor_directories(start_directory: str, filename: str):
    current_directory = os.path.abspath(start_directory)
    while True:
        candidate_path = os.path.join(current_directory, filename)
        if os.path.exists(candidate_path):
            return candidate_path
        parent_directory = os.path.dirname(current_directory)
        if parent_directory == current_directory:
            return None
        current_directory = parent_directory


def repository_declares_conflicting_formatter(
    file_path: str, file_extension: str
) -> bool:
    start_directory = os.path.dirname(os.path.abspath(file_path)) or "."
    if file_extension == ".py":
        pyproject_path = find_file_in_ancestor_directories(
            start_directory, "pyproject.toml"
        )
        if pyproject_path:
            try:
                with open(pyproject_path) as pyproject_file:
                    pyproject_text = pyproject_file.read()
            except OSError:
                pyproject_text = ""
            if "[tool.black]" in pyproject_text and "[tool.ruff" not in pyproject_text:
                return True
    if file_extension in (".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml"):
        for biome_config_name in ("biome.json", "biome.jsonc"):
            if find_file_in_ancestor_directories(start_directory, biome_config_name):
                return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    try:
        if os.path.getsize(file_path) > 1024 * 1024:
            sys.exit(0)
    except OSError:
        sys.exit(0)

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in FORMATTERS:
        sys.exit(0)

    if repository_declares_conflicting_formatter(file_path, ext):
        sys.exit(0)

    for formatter in FORMATTERS[ext]["formatters"]:
        if check_formatter_available(formatter["cmd"]):
            run_formatter(file_path, formatter)
            sys.exit(0)

    missing_names = [f["name"] for f in FORMATTERS[ext]["formatters"]]
    names = ", ".join(missing_names)
    message = f"No formatters for {ext} files. Install: {names}"
    print(json.dumps({"continue": True, "systemMessage": message}))
    sys.exit(0)


if __name__ == "__main__":
    main()
