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
end_of_work_compliance_review_module = import_hyphenated_hook_module(
    "end-of-work-compliance-review"
)
import end_of_work_compliance_review_logging as end_of_work_compliance_review_logging_module  # noqa: E402


@pytest.fixture
def reset_session_id_prefix_between_tests():
    end_of_work_compliance_review_module.set_session_id_short_prefix("")
    yield
    end_of_work_compliance_review_module.set_session_id_short_prefix("")


@pytest.fixture
def isolate_persistent_log_file(tmp_path, monkeypatch):
    isolated_log_path = tmp_path / "logs" / "end-of-work-compliance-review.log"
    monkeypatch.setattr(
        end_of_work_compliance_review_logging_module,
        "PERSISTENT_LOG_FILE_PATH",
        isolated_log_path,
    )
    return isolated_log_path


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
