import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

background_bash_anti_pattern_validator_handler = import_hyphenated_hook_module(
    "background_bash_anti_pattern_validator_handler"
)


def background(command):
    return background_bash_anti_pattern_validator_handler.handle(
        {
            "tool_name": "Bash",
            "tool_input": {"command": command, "run_in_background": True},
        }
    )


def foreground(command):
    return background_bash_anti_pattern_validator_handler.handle(
        {
            "tool_name": "Bash",
            "tool_input": {"command": command, "run_in_background": False},
        }
    )


def test_backgrounded_rebuild_is_denied_rather_than_advised():
    result = background("rebuild 2>&1 | tail -40")
    assert result is not None
    assert result.decision == "deny"
    assert "launch-command-detached-into-new-session" in result.reason


def test_backgrounded_service_restart_is_denied():
    result = background("systemctl --user restart syncthing")
    assert result is not None
    assert result.decision == "deny"


def test_the_sanctioned_detached_launch_is_not_denied():
    assert (
        background("launch-command-detached-into-new-session /tmp/log rebuild") is None
    )


def test_a_foreground_rebuild_is_untouched():
    assert foreground("rebuild") is None


def test_polling_a_log_for_a_success_marker_is_untouched():
    assert (
        background(
            'for i in $(seq 1 40); do if grep -qi "rebuild complete" /tmp/out; '
            "then break; fi; sleep 15; done"
        )
        is None
    )
