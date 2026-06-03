import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HOOKS_DIRECTORY = Path(__file__).resolve().parent.parent


def find_hook_module_path(hyphenated_name):
    candidate_module_paths = [
        candidate
        for candidate in HOOKS_DIRECTORY.rglob(f"{hyphenated_name}.py")
        if "tests" not in candidate.parts and "__pycache__" not in candidate.parts
    ]
    if not candidate_module_paths:
        raise FileNotFoundError(f"hook script not found: {hyphenated_name}.py")
    return candidate_module_paths[0]


def import_hyphenated_hook_module(hyphenated_name):
    module_path = find_hook_module_path(hyphenated_name)
    spec = importlib.util.spec_from_file_location(
        hyphenated_name.replace("-", "_"), module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[hyphenated_name.replace("-", "_")] = module
    spec.loader.exec_module(module)
    return module


import_hyphenated_hook_module("session-context")
import_hyphenated_hook_module("monitor-streaming-pattern-validator")
import_hyphenated_hook_module("memory-recall")


PROHIBITED_COMMAND_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "prohibited-command-guard"
)
LINE_COUNT_ADVISORY_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "line-count-advisory-guard"
)


@pytest.fixture
def invoke_prohibited_command_guard_hook():
    def runner(payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PROHIBITED_COMMAND_GUARD_HOOK_SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=5,
        )

    return runner


@pytest.fixture
def parse_prohibited_command_guard_system_message():
    def parser(stdout: str) -> str:
        parsed = json.loads(stdout)
        return parsed.get("systemMessage", "")

    return parser


@pytest.fixture
def invoke_prohibited_command_guard_hook_with_raw_stdin():
    def runner(raw_stdin: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PROHIBITED_COMMAND_GUARD_HOOK_SCRIPT_PATH)],
            input=raw_stdin,
            capture_output=True,
            text=True,
            timeout=5,
        )

    return runner


PROHIBITED_WORDS_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "prohibited-words-guard"
)


def run_prohibited_words_guard(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROHIBITED_WORDS_GUARD_HOOK_SCRIPT_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
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
    def runner(payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(LINE_COUNT_ADVISORY_GUARD_HOOK_SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=5,
        )

    return runner


AGENT_INSTRUCTION_FILE_AUTHORING_ROUTER_HOOK_SCRIPT_PATH = find_hook_module_path(
    "agent-instruction-file-authoring-router"
)


@pytest.fixture
def invoke_agent_instruction_file_authoring_router_hook(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "AGENT_INSTRUCTION_AUTHORING_ROUTER_STATE_DIRECTORY", str(tmp_path)
    )

    def runner(payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(AGENT_INSTRUCTION_FILE_AUTHORING_ROUTER_HOOK_SCRIPT_PATH),
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=5,
        )

    return runner


MEMORY_RECALL_HOOK_SCRIPT_PATH = find_hook_module_path("memory-recall")


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
    def run_hook_with_payload(payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MEMORY_RECALL_HOOK_SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=5,
        )

    return run_hook_with_payload
