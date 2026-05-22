import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "pre-tool-use"
    / "background-bash-anti-pattern-validator.py"
)


def _invoke_validator_with_payload(payload):
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
    )


def _invoke_validator_with_raw_stdin(raw_stdin):
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT_PATH)],
        input=raw_stdin,
        capture_output=True,
        text=True,
        timeout=5,
    )


class TestHookEndToEndViaSubprocess:
    def test_denies_background_bash_with_until_zero_count_loop(self):
        result = _invoke_validator_with_payload(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": 'until [ "$(gh run list --json status --jq length)" = "0" ]; do sleep 15; done',
                    "run_in_background": True,
                },
            }
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert (
            "until-loop-terminating-on-empty-count"
            in parsed["hookSpecificOutput"]["permissionDecisionReason"]
        )

    def test_allows_foreground_bash_with_same_command(self):
        result = _invoke_validator_with_payload(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": 'until [ "$(gh run list --json status --jq length)" = "0" ]; do sleep 15; done',
                    "run_in_background": False,
                },
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_background_bash_with_safe_polling_pattern(self):
        safe_command = (
            "for i in $(seq 1 60); do "
            'matched=$(gh run list --json headSha --jq "[.[] | select(.headSha == \\"$SHA\\")] | length"); '
            '[ "$matched" -gt 0 ] || { echo "no runs match"; exit 1; }; '
            "sleep 15; done"
        )
        result = _invoke_validator_with_payload(
            {
                "tool_name": "Bash",
                "tool_input": {"command": safe_command, "run_in_background": True},
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_ignores_non_bash_tool(self):
        result = _invoke_validator_with_payload(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": "/etc/hosts"},
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_ignores_malformed_input(self):
        result = _invoke_validator_with_raw_stdin("not json")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_denies_background_bash_with_jq_literal_count_test(self):
        command_with_jq_literal_count = (
            "gh run list --json headSha --jq "
            "'[.[] | select(.headSha == "
            '"1e42771447c81fb6a96b2d3eef3e16df9f8517b3")] | length\''
            " | xargs -I {} test {} = 0"
        )
        result = _invoke_validator_with_payload(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": command_with_jq_literal_count,
                    "run_in_background": True,
                },
            }
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
