import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
import_hyphenated_hook_module("memory_recall_memory_directory")

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
    monkeypatch.setenv(
        "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY", str(tmp_path)
    )

    def runner(payload: dict):
        return run_hook_subprocess(
            PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH,
            json.dumps({**payload, "hook_event_name": "PreToolUse"}),
        )

    return runner


@pytest.fixture
def invoke_record_instructions_skill_invocation_hook(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY", str(tmp_path)
    )

    def runner(payload: dict):
        return run_hook_subprocess(
            POST_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH,
            json.dumps({**payload, "hook_event_name": "PostToolUse"}),
        )

    return runner


@pytest.fixture
def isolated_memory_recall_environment(tmp_path, monkeypatch):
    fake_home_directory = tmp_path / "fake-home"
    fake_home_directory.mkdir()
    debounce_state_directory = tmp_path / "debounce-state"
    debounce_state_directory.mkdir()
    monkeypatch.setenv("HOME", str(fake_home_directory))
    monkeypatch.setenv(
        "MEMORY_RECALL_DEBOUNCE_STATE_DIRECTORY", str(debounce_state_directory)
    )
    return fake_home_directory, debounce_state_directory


@pytest.fixture
def make_memory_recall_directory():
    def create_memory_directory_for_workspace(fake_home_directory, workspace_directory):
        import memory_recall_memory_directory

        memory_directory = (
            memory_recall_memory_directory.resolve_memory_directory_for_cwd(
                str(workspace_directory)
            )
        )
        memory_directory.mkdir(parents=True, exist_ok=True)
        return memory_directory

    return create_memory_directory_for_workspace


@pytest.fixture
def invoke_memory_recall_hook():
    def run_hook_with_payload(payload: dict):
        return run_hook_subprocess(
            PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH, json.dumps(payload)
        )

    return run_hook_with_payload
