import json

from notify_codex_turn_complete_test_support import run_notifier


def test_turn_completion_uses_the_request_as_title_and_result_as_body(tmp_path):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "input-messages": ["Check every ARR container and report health"],
            "last-assistant-message": "All 11 ARR containers remain\n  running.",
        }
    )

    notifier_run = run_notifier(tmp_path, payload)

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert notifier_run.notification_arguments == [
        "--app-name",
        "Codex",
        "--action=default=Focus session",
        "--wait",
        "Codex · Check every ARR container and report health",
        "All 11 ARR containers remain running.",
    ]


def test_missing_event_text_falls_back_to_the_working_directory(tmp_path):
    project_directory = tmp_path / "dotfiles"
    project_directory.mkdir()
    payload = json.dumps({"type": "agent-turn-complete"})

    notifier_run = run_notifier(tmp_path, payload, working_directory=project_directory)

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert notifier_run.notification_arguments[-2:] == [
        "Codex · dotfiles",
        "Turn complete",
    ]


def test_long_event_text_is_bounded(tmp_path):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "input-messages": ["request " * 30],
            "last-assistant-message": "result " * 100,
        }
    )

    notifier_run = run_notifier(tmp_path, payload)

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert len(notifier_run.notification_arguments[-2]) <= 100
    assert len(notifier_run.notification_arguments[-1]) <= 320
    assert notifier_run.notification_arguments[-2].endswith("…")
    assert notifier_run.notification_arguments[-1].endswith("…")


def test_malformed_or_unknown_events_do_not_notify(tmp_path):
    for payload in ("not-json", json.dumps({"type": "approval-requested"})):
        notifier_run = run_notifier(tmp_path, payload)

        assert notifier_run.result.returncode == 0, notifier_run.result.stderr
        assert notifier_run.notification_arguments == []
