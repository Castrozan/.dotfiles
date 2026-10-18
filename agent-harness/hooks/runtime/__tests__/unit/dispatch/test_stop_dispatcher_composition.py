import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hook_module_loader import import_hyphenated_hook_module

stop_dispatcher = import_hyphenated_hook_module("stop-dispatcher")


def test_stop_dispatcher_composes_only_active_handlers():
    handler_module_names = {
        handler.handler_module_name for handler in stop_dispatcher.STOP_HANDLERS
    }
    assert handler_module_names == {
        "nix_rebuild_reminder_handler",
        "end_of_turn_format_guard_handler",
        "herdr_agent_session_report_handler",
    }


@pytest.mark.parametrize(
    "guard_decision, cleanup_decision", [("block", None), (None, "block"), (None, None)]
)
def test_browser_cleanup_only_runs_after_guards_and_before_completion(
    monkeypatch, guard_decision, cleanup_decision
):
    calls = []
    emitted = []
    monkeypatch.setattr(
        stop_dispatcher,
        "dispatched_hook_input_or_exit",
        lambda events: {"hook_event_name": "Stop"},
    )
    monkeypatch.setattr(stop_dispatcher, "requested_hook_surface", lambda: "codex")
    monkeypatch.setattr(stop_dispatcher, "emit_stop_decision", emitted.append)

    def run_handlers(payload, handlers, surface):
        calls.append(handlers)
        decision = (
            guard_decision
            if handlers is stop_dispatcher.STOP_HANDLERS
            else cleanup_decision
        )
        return SimpleNamespace(decision=decision)

    monkeypatch.setattr(stop_dispatcher, "run_handlers", run_handlers)
    with pytest.raises(SystemExit):
        stop_dispatcher.main()
    if guard_decision:
        assert calls == [stop_dispatcher.STOP_HANDLERS]
    elif cleanup_decision:
        assert calls == [
            stop_dispatcher.STOP_HANDLERS,
            [stop_dispatcher.BROWSER_CLEANUP_HANDLER],
        ]
    else:
        assert calls == [
            stop_dispatcher.STOP_HANDLERS,
            [stop_dispatcher.BROWSER_CLEANUP_HANDLER],
            stop_dispatcher.COMPLETION_HANDLERS,
        ]
    assert emitted[0].decision == (guard_decision or cleanup_decision)
