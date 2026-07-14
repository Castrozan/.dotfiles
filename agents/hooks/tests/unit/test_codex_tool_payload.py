import importlib.util
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
CODEX_TOOL_PAYLOAD_SOURCE = HOOKS_ROOT / "common" / "codex_tool_payload.py"

_spec = importlib.util.spec_from_file_location(
    "codex_tool_payload", CODEX_TOOL_PAYLOAD_SOURCE
)
codex_tool_payload = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(codex_tool_payload)

normalize_codex_tool_payload = codex_tool_payload.normalize_codex_tool_payload


def test_codex_shell_command_list_becomes_bash_string():
    normalized = normalize_codex_tool_payload(
        {"tool_name": "shell", "tool_input": {"command": ["git", "add", "-A"]}}
    )
    assert normalized["tool_name"] == "Bash"
    assert normalized["tool_input"]["command"] == "git add -A"


def test_codex_shell_quotes_arguments_with_spaces():
    normalized = normalize_codex_tool_payload(
        {
            "tool_name": "shell",
            "tool_input": {"command": ["git", "commit", "-m", "a b"]},
        }
    )
    assert normalized["tool_input"]["command"] == "git commit -m 'a b'"


def test_claude_bash_payload_is_unchanged():
    payload = {"tool_name": "Bash", "tool_input": {"command": "git add -A"}}
    assert normalize_codex_tool_payload(payload) == payload


def test_apply_patch_shell_call_is_left_untouched():
    payload = {
        "tool_name": "shell",
        "tool_input": {"command": ["apply_patch", "*** Begin Patch\n*** End Patch"]},
    }
    assert normalize_codex_tool_payload(payload) == payload


def test_non_shell_tool_is_left_untouched():
    payload = {"tool_name": "apply_patch", "tool_input": {"input": "x"}}
    assert normalize_codex_tool_payload(payload) == payload
