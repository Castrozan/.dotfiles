import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import (
    find_hook_module_path,
    import_hyphenated_hook_module,
    run_hook_subprocess,
)

import_hyphenated_hook_module("session-context")
import_hyphenated_hook_module("monitor-streaming-pattern-validator")
import_hyphenated_hook_module("memory-recall")

PROHIBITED_COMMAND_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "prohibited-command-guard"
)
PROHIBITED_WORDS_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "prohibited-words-guard"
)
LINE_COUNT_ADVISORY_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "line-count-advisory-guard"
)
AGENT_INSTRUCTION_FILE_AUTHORING_ROUTER_HOOK_SCRIPT_PATH = find_hook_module_path(
    "agent-instruction-file-authoring-router"
)
RECORD_INSTRUCTIONS_SKILL_INVOCATION_HOOK_SCRIPT_PATH = find_hook_module_path(
    "record-instructions-skill-invocation"
)
MEMORY_RECALL_HOOK_SCRIPT_PATH = find_hook_module_path("memory-recall")


@pytest.fixture
def invoke_prohibited_command_guard_hook():
    def runner(payload: dict):
        return run_hook_subprocess(
            PROHIBITED_COMMAND_GUARD_HOOK_SCRIPT_PATH, json.dumps(payload)
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
        return run_hook_subprocess(PROHIBITED_COMMAND_GUARD_HOOK_SCRIPT_PATH, raw_stdin)

    return runner


def run_prohibited_words_guard(payload: dict):
    return run_hook_subprocess(
        PROHIBITED_WORDS_GUARD_HOOK_SCRIPT_PATH, json.dumps(payload)
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
def invoke_line_count_advisory_guard_hook():
    def runner(payload: dict):
        return run_hook_subprocess(
            LINE_COUNT_ADVISORY_GUARD_HOOK_SCRIPT_PATH, json.dumps(payload)
        )

    return runner


@pytest.fixture
def invoke_agent_instruction_file_authoring_router_hook(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY", str(tmp_path)
    )

    def runner(payload: dict):
        return run_hook_subprocess(
            AGENT_INSTRUCTION_FILE_AUTHORING_ROUTER_HOOK_SCRIPT_PATH,
            json.dumps(payload),
        )

    return runner


@pytest.fixture
def invoke_record_instructions_skill_invocation_hook(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY", str(tmp_path)
    )

    def runner(payload: dict):
        return run_hook_subprocess(
            RECORD_INSTRUCTIONS_SKILL_INVOCATION_HOOK_SCRIPT_PATH, json.dumps(payload)
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
        import memory_recall

        memory_directory = memory_recall.resolve_memory_directory_for_cwd(
            str(workspace_directory)
        )
        memory_directory.mkdir(parents=True, exist_ok=True)
        return memory_directory

    return create_memory_directory_for_workspace


@pytest.fixture
def invoke_memory_recall_hook():
    def run_hook_with_payload(payload: dict):
        return run_hook_subprocess(MEMORY_RECALL_HOOK_SCRIPT_PATH, json.dumps(payload))

    return run_hook_with_payload
