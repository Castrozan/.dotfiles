import json

from notify_codex_turn_complete_test_support import run_notifier


def test_default_action_focuses_wezterm_then_the_matching_herdr_session(tmp_path):
    thread_id = "01a04dbd-4d12-74e2-bb8a-8d7f6bc69be7"
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": thread_id,
            "input-messages": ["Check every ARR container"],
            "last-assistant-message": "All containers are healthy.",
        }
    )
    environment = {
        "NOTIFICATION_ACTION": "default",
        "HYPRLAND_CLIENTS_JSON": json.dumps(
            [
                {
                    "address": "0xolder",
                    "class": "org.wezfurlong.wezterm",
                    "focusHistoryID": 4,
                    "mapped": True,
                    "hidden": False,
                    "workspace": {"id": 11},
                },
                {
                    "address": "0xrecent",
                    "class": "org.wezfurlong.wezterm",
                    "focusHistoryID": 1,
                    "mapped": True,
                    "hidden": False,
                    "workspace": {"id": 11},
                },
            ]
        ),
        "HERDR_AGENT_LIST_JSON": json.dumps(
            {
                "result": {
                    "agents": [
                        {
                            "agent_session": {"value": "different-thread"},
                            "pane_id": "wM:pwrong",
                        },
                        {
                            "agent_session": {"value": thread_id},
                            "pane_id": "wM:p7",
                        },
                    ]
                }
            }
        ),
    }

    notifier_run = run_notifier(tmp_path, payload, environment=environment)

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert notifier_run.desktop_focus_log_path.read_text(
        encoding="utf-8"
    ).splitlines() == [
        "dispatch",
        "focuswindow",
        "address:0xrecent",
    ]
    assert notifier_run.herdr_log_path.read_text(encoding="utf-8").splitlines() == [
        "agent",
        "focus",
        "wM:p7",
    ]


def test_default_action_does_not_move_herdr_without_current_workspace_wezterm(
    tmp_path,
):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": "thread-id",
        }
    )

    notifier_run = run_notifier(
        tmp_path, payload, environment={"NOTIFICATION_ACTION": "default"}
    )

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert not notifier_run.herdr_log_path.exists()


def test_expired_session_notification_does_not_focus_an_unrelated_wezterm(
    tmp_path,
):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": "expired-thread",
        }
    )
    environment = {
        "NOTIFICATION_ACTION": "default",
        "HYPRLAND_CLIENTS_JSON": json.dumps(
            [
                {
                    "address": "0xwezterm",
                    "class": "org.wezfurlong.wezterm",
                    "focusHistoryID": 0,
                    "mapped": True,
                    "hidden": False,
                    "workspace": {"id": 11},
                }
            ]
        ),
    }

    notifier_run = run_notifier(tmp_path, payload, environment=environment)

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert not notifier_run.desktop_focus_log_path.exists()
    assert not notifier_run.herdr_log_path.exists()


def test_dismissed_notification_does_not_focus_wezterm_or_herdr(tmp_path):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": "thread-id",
        }
    )
    environment = {
        "HYPRLAND_CLIENTS_JSON": json.dumps(
            [
                {
                    "address": "0xwezterm",
                    "class": "org.wezfurlong.wezterm",
                    "focusHistoryID": 0,
                    "mapped": True,
                    "hidden": False,
                    "workspace": {"id": 11},
                }
            ]
        ),
        "HERDR_AGENT_LIST_JSON": json.dumps(
            {
                "result": {
                    "agents": [
                        {
                            "agent_session": {"value": "thread-id"},
                            "pane_id": "wM:p7",
                        }
                    ]
                }
            }
        ),
    }

    notifier_run = run_notifier(tmp_path, payload, environment=environment)

    assert notifier_run.result.returncode == 0, notifier_run.result.stderr
    assert not notifier_run.desktop_focus_log_path.exists()
    assert not notifier_run.herdr_log_path.exists()
