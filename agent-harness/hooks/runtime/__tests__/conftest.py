import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[3] / "harnesses" / "clawde" / "scripts"),
)

HOOKS_ROOT = Path(__file__).resolve().parent.parent
DIRECTORIES_EXCLUDED_FROM_DEPLOY = ("__pycache__", "__tests__")
for hook_module_directory in HOOKS_ROOT.rglob("*"):
    if hook_module_directory.is_dir() and not any(
        excluded in hook_module_directory.parts
        for excluded in DIRECTORIES_EXCLUDED_FROM_DEPLOY
    ):
        sys.path.insert(0, str(hook_module_directory))

from hook_module_loader import (  # noqa: E402
    find_hook_module_path,
    import_hyphenated_hook_module,
    run_hook_subprocess,
)

import_hyphenated_hook_module("session-start-dispatcher")
import_hyphenated_hook_module("monitor_streaming_pattern_validator_handler")

POST_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH = find_hook_module_path(
    "post-tool-use-dispatcher"
)
PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH = find_hook_module_path(
    "pre-tool-use-dispatcher"
)


@pytest.fixture
def invoke_prohibited_command_guard_hook():
    def runner(payload: dict):
        return run_hook_subprocess(
            PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH, json.dumps(payload)
        )

    return runner


@pytest.fixture
def parse_prohibited_command_guard_system_message():
    def parser(stdout: str) -> str:
        return json.loads(stdout).get("systemMessage", "")

    return parser


@pytest.fixture
def invoke_prohibited_command_guard_hook_with_raw_stdin():
    def runner(raw_stdin: str):
        return run_hook_subprocess(PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH, raw_stdin)

    return runner


def run_prohibited_words_guard(payload: dict):
    return run_hook_subprocess(
        PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH, json.dumps(payload)
    )


@pytest.fixture
def invoke_prohibited_words_guard_hook(tmp_path, monkeypatch):
    wordlist_file = tmp_path / "prohibited-words.txt"
    wordlist_file.write_text("# fake words\nacme\ninitech\n", encoding="utf-8")
    monkeypatch.setenv("PROHIBITED_WORDS_FILE", str(wordlist_file))
    return run_prohibited_words_guard


@pytest.fixture
def invoke_prohibited_words_guard_hook_without_wordlist(tmp_path, monkeypatch):
    monkeypatch.setenv("PROHIBITED_WORDS_FILE", str(tmp_path / "missing-wordlist.txt"))
    return run_prohibited_words_guard


@pytest.fixture
def invoke_agent_instruction_file_authoring_router_hook(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    def runner(payload: dict):
        return run_hook_subprocess(
            PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH,
            json.dumps({**payload, "hook_event_name": "PreToolUse"}),
        )

    return runner


@pytest.fixture
def invoke_documentation_authoring_router_hook(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    def runner(payload: dict):
        return run_hook_subprocess(
            PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH,
            json.dumps({**payload, "hook_event_name": "PreToolUse"}),
        )

    return runner


@pytest.fixture
def invoke_record_skill_invocation_hook(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    def runner(payload: dict):
        return run_hook_subprocess(
            POST_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH,
            json.dumps({**payload, "hook_event_name": "PostToolUse"}),
        )

    return runner
