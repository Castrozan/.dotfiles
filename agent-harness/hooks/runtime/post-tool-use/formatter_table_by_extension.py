from __future__ import annotations

FORMATTERS_BY_FILE_EXTENSION = {
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
