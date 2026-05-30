import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT_PATH = next(
    Path(__file__).resolve().parent.parent.parent.rglob("line-count-advisory-guard.py")
)


def invoke_hook_with_payload(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
    )


def write_python_file_with_line_count(
    parent_directory: Path, file_basename: str, line_count: int
) -> Path:
    file_path = parent_directory / file_basename
    file_path.write_text("\n".join(f"line_{n}" for n in range(line_count)) + "\n")
    return file_path


def parse_hook_stdout(stdout: str) -> dict:
    return json.loads(stdout)


class TestLineCountThresholds:
    def test_silent_under_advisory_threshold(self, tmp_path):
        file_path = write_python_file_with_line_count(tmp_path, "small.py", 50)
        result = invoke_hook_with_payload(
            {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_silent_at_advisory_threshold_boundary(self, tmp_path):
        file_path = write_python_file_with_line_count(tmp_path, "boundary.py", 100)
        result = invoke_hook_with_payload(
            {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_advises_above_advisory_threshold(self, tmp_path):
        file_path = write_python_file_with_line_count(tmp_path, "medium.py", 120)
        result = invoke_hook_with_payload(
            {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        payload = parse_hook_stdout(result.stdout)
        assert "ADVISORY" in payload["systemMessage"]
        assert "120" in payload["systemMessage"]
        assert "decision" not in payload

    def test_warns_above_warning_threshold(self, tmp_path):
        file_path = write_python_file_with_line_count(tmp_path, "large.py", 170)
        result = invoke_hook_with_payload(
            {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        payload = parse_hook_stdout(result.stdout)
        assert "WARNING" in payload["systemMessage"]
        assert "170" in payload["systemMessage"]
        assert "decision" not in payload

    def test_blocks_above_blocking_threshold(self, tmp_path):
        file_path = write_python_file_with_line_count(tmp_path, "huge.py", 250)
        result = invoke_hook_with_payload(
            {"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        payload = parse_hook_stdout(result.stdout)
        assert payload["decision"] == "block"
        assert "250" in payload["reason"]
        assert "BLOCKED" in payload["systemMessage"]


class TestFileTypeFiltering:
    @pytest.mark.parametrize(
        "file_basename",
        [
            "doc.md",
            "config.json",
            "config.yaml",
            "data.toml",
            "package-lock.json",
            "Cargo.lock",
            "image.svg",
            "page.html",
            "notes.txt",
        ],
    )
    def test_skips_non_code_extensions(self, tmp_path, file_basename):
        file_path = write_python_file_with_line_count(tmp_path, file_basename, 500)
        result = invoke_hook_with_payload(
            {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    @pytest.mark.parametrize(
        "file_basename",
        [
            "script.py",
            "module.nix",
            "tool.sh",
            "component.tsx",
            "main.go",
            "lib.rs",
        ],
    )
    def test_acts_on_code_extensions(self, tmp_path, file_basename):
        file_path = write_python_file_with_line_count(tmp_path, file_basename, 250)
        result = invoke_hook_with_payload(
            {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        payload = parse_hook_stdout(result.stdout)
        assert payload["decision"] == "block"


class TestNonApplicableToolNames:
    @pytest.mark.parametrize(
        "tool_name",
        ["Bash", "Read", "Grep", "Glob", "WebFetch"],
    )
    def test_ignores_unrelated_tools(self, tmp_path, tool_name):
        file_path = write_python_file_with_line_count(tmp_path, "irrelevant.py", 500)
        result = invoke_hook_with_payload(
            {"tool_name": tool_name, "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestMissingOrInvalidInputs:
    def test_silent_when_file_does_not_exist(self, tmp_path):
        file_path = tmp_path / "never_written.py"
        result = invoke_hook_with_payload(
            {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_silent_when_file_path_missing(self):
        result = invoke_hook_with_payload({"tool_name": "Write", "tool_input": {}})
        assert result.returncode == 0
        assert result.stdout == ""

    def test_exits_zero_silently_on_invalid_json(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT_PATH)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestNotebookEditPathField:
    def test_uses_notebook_path_for_notebook_edit(self, tmp_path):
        file_path = write_python_file_with_line_count(tmp_path, "notebook.py", 250)
        result = invoke_hook_with_payload(
            {
                "tool_name": "NotebookEdit",
                "tool_input": {"notebook_path": str(file_path)},
            }
        )
        assert result.returncode == 0
        payload = parse_hook_stdout(result.stdout)
        assert payload["decision"] == "block"
