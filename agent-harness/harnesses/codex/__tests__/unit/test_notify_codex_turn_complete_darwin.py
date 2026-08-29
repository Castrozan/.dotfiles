import json

import pytest

from notify_codex_turn_complete_test_support import run_notifier


def test_darwin_notification_is_readable_and_offers_a_focus_action(tmp_path):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": "thread-id",
            "input-messages": ["Check every ARR container"],
            "last-assistant-message": "All containers are healthy.",
        }
    )

    notifier_run = run_notifier(tmp_path, payload, platform="darwin")

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert notifier_run.notification_arguments == [
        "--title",
        "Codex · Check every ARR container",
        "--message",
        "All containers are healthy.",
        "--actions",
        "Focus session",
        "--close-label",
        "Dismiss",
        "--timeout",
        "3600",
        "--group",
        "thread-id",
    ]


@pytest.mark.parametrize(
    "notification_action",
    ["@CONTENTCLICKED", "@ACTIONCLICKED", "Focus session"],
)
def test_darwin_click_summons_wezterm_then_focuses_matching_herdr_pane(
    tmp_path, notification_action
):
    thread_identifier = "01a04dbd-4d12-74e2-bb8a-8d7f6bc69be7"
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": thread_identifier,
        }
    )
    notifier_run = run_notifier(
        tmp_path,
        payload,
        platform="darwin",
        environment={
            "NOTIFICATION_ACTION": notification_action,
            "HERDR_AGENT_LIST_JSON": json.dumps(
                {
                    "result": {
                        "agents": [
                            {
                                "agent_session": {"value": thread_identifier},
                                "pane_id": "wM:p7",
                            }
                        ]
                    }
                }
            ),
        },
    )

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert notifier_run.desktop_focus_log_path.read_text(
        encoding="utf-8"
    ).splitlines() == ["-c", "summonWezTermToCurrentWorkspace()"]
    assert notifier_run.herdr_log_path.read_text(encoding="utf-8").splitlines() == [
        "agent",
        "focus",
        "wM:p7",
    ]
