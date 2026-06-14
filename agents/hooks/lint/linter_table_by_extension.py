from __future__ import annotations


RUFF_SUMMARY_LINE_PREFIXES = ("Found", "All checks passed")


def parse_ruff_output(output: str) -> list[str]:
    return [
        line
        for line in output.split("\n")
        if line.strip() and not line.startswith(RUFF_SUMMARY_LINE_PREFIXES)
    ]


def parse_eslint_output(output: str) -> list[str]:
    return [
        line for line in output.split("\n") if "Error" in line or "Warning" in line
    ][:5]


def parse_tsc_output(output: str) -> list[str]:
    return [line for line in output.split("\n") if "error TS" in line][:5]


def parse_statix_output(output: str) -> list[str]:
    return [line for line in output.split("\n") if ">" in line or "Warning" in line][:5]


def parse_deadnix_output(output: str) -> list[str]:
    return [line for line in output.split("\n") if line.strip()][:5]


def parse_shellcheck_output(output: str) -> list[str]:
    return [
        line
        for line in output.split("\n")
        if "error:" in line.lower() or "warning:" in line.lower()
    ][:5]


def parse_clippy_output(output: str) -> list[str]:
    return [
        line for line in output.split("\n") if "warning:" in line or "error:" in line
    ][:5]


def parse_generic_nonempty_output(output: str) -> list[str]:
    return output.strip().split("\n")[:5] if output.strip() else []


LINTERS_BY_FILE_EXTENSION: dict[str, list[dict]] = {
    ".py": [
        {
            "cmd": ["ruff", "check", "--select=E,F,W"],
            "name": "ruff",
            "parse": parse_ruff_output,
        },
    ],
    ".js": [
        {
            "cmd": ["eslint", "--format=compact"],
            "name": "eslint",
            "parse": parse_eslint_output,
        },
    ],
    ".ts": [
        {
            "cmd": ["eslint", "--format=compact"],
            "name": "eslint",
            "parse": parse_eslint_output,
        },
        {
            "cmd": ["tsc", "--noEmit"],
            "name": "tsc",
            "parse": parse_tsc_output,
        },
    ],
    ".tsx": [
        {
            "cmd": ["eslint", "--format=compact"],
            "name": "eslint",
            "parse": parse_eslint_output,
        },
    ],
    ".nix": [
        {
            "cmd": ["statix", "check"],
            "name": "statix",
            "parse": parse_statix_output,
        },
        {
            "cmd": ["deadnix"],
            "name": "deadnix",
            "parse": parse_deadnix_output,
        },
    ],
    ".sh": [
        {
            "cmd": ["shellcheck", "--format=gcc"],
            "name": "shellcheck",
            "parse": parse_shellcheck_output,
        },
    ],
    ".rs": [
        {
            "cmd": ["cargo", "clippy", "--message-format=short", "-q"],
            "name": "clippy",
            "parse": parse_clippy_output,
        },
    ],
    ".go": [
        {
            "cmd": ["go", "vet"],
            "name": "go vet",
            "parse": parse_generic_nonempty_output,
        },
        {
            "cmd": ["staticcheck"],
            "name": "staticcheck",
            "parse": parse_generic_nonempty_output,
        },
    ],
}
