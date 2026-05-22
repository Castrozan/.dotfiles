def parse_ruff_output(out: str) -> list[str]:
    return [
        line
        for line in out.split("\n")
        if line.strip()
        and not line.startswith("Found")
        and not line.startswith("All checks passed")
    ]


def parse_eslint_output(out: str) -> list[str]:
    return [line for line in out.split("\n") if "Error" in line or "Warning" in line][
        :5
    ]


def parse_tsc_output(out: str) -> list[str]:
    return [line for line in out.split("\n") if "error TS" in line][:5]


def parse_statix_output(out: str) -> list[str]:
    return [line for line in out.split("\n") if ">" in line or "Warning" in line][:5]


def parse_deadnix_output(out: str) -> list[str]:
    return [line for line in out.split("\n") if line.strip()][:5]


def parse_shellcheck_output(out: str) -> list[str]:
    return [
        line
        for line in out.split("\n")
        if "error:" in line.lower() or "warning:" in line.lower()
    ][:5]


def parse_clippy_output(out: str) -> list[str]:
    return [line for line in out.split("\n") if "warning:" in line or "error:" in line][
        :5
    ]


def parse_go_tool_output(out: str) -> list[str]:
    return out.strip().split("\n")[:5] if out.strip() else []


LINTER_COMMANDS_BY_FILE_EXTENSION = {
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
            "parse": parse_go_tool_output,
        },
        {
            "cmd": ["staticcheck"],
            "name": "staticcheck",
            "parse": parse_go_tool_output,
        },
    ],
}
