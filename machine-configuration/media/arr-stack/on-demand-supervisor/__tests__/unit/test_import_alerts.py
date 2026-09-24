import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor")
)

import import_alerts
import pytest


def configuration(tmp_path):
    return {
        "disk_guard": {"alert_state_file": str(tmp_path / "disk.json")},
        "radarr_url": "http://radarr",
        "sonarr_url": "http://sonarr",
        "radarr_config_file": "radarr.xml",
        "sonarr_config_file": "sonarr.xml",
    }


def stub_queues(monkeypatch):
    monkeypatch.setattr(
        import_alerts, "read_arr_api_key_from_config_xml", lambda path: "key"
    )
    monkeypatch.setattr(
        import_alerts,
        "queued_records",
        lambda *args: [
            {
                "downloadId": "torrent",
                "title": "Unmatched",
                "size": 1024**3,
                "trackedDownloadState": "importPending",
                "statusMessages": [{"messages": ["Title mismatch"]}],
            }
        ],
    )


def test_alert_includes_reason_size_and_management_link(monkeypatch, tmp_path):
    stub_queues(monkeypatch)
    messages = []
    monkeypatch.setattr(
        import_alerts,
        "deliver_alert_message_best_effort",
        lambda build, config, label: messages.append(build()) or True,
    )
    config = configuration(tmp_path)
    config["disk_guard"].update(
        email_sender="arr@example.test", email_recipient="owner@example.test"
    )
    import_alerts.maybe_alert_blocked_imports(config, 100000, False)
    body = messages[0].get_content()
    assert "Title mismatch" in body
    assert "1.0 GiB" in body
    assert "http://sonarr/activity/queue" in body
    import_alerts.maybe_alert_blocked_imports(config, 100001, False)
    assert len(messages) == 1


def test_failed_delivery_retries_and_dry_run_never_sends(monkeypatch, tmp_path):
    stub_queues(monkeypatch)
    calls = []
    monkeypatch.setattr(
        import_alerts,
        "deliver_alert_message_best_effort",
        lambda *args: calls.append(True) or False,
    )
    config = configuration(tmp_path)
    import_alerts.maybe_alert_blocked_imports(config, 100000, True)
    assert calls == []
    import_alerts.maybe_alert_blocked_imports(config, 100000, False)
    import_alerts.maybe_alert_blocked_imports(config, 100001, False)
    assert len(calls) == 2


def test_unavailable_or_empty_queues_do_not_send(monkeypatch, tmp_path):
    stub_queues(monkeypatch)
    monkeypatch.setattr(import_alerts, "queued_records", lambda *args: None)
    calls = []
    monkeypatch.setattr(
        import_alerts,
        "deliver_alert_message_best_effort",
        lambda *args: calls.append(True),
    )
    import_alerts.maybe_alert_blocked_imports(configuration(tmp_path), 100000, False)
    assert calls == []


@pytest.mark.parametrize("error", [FileNotFoundError(), ValueError()])
def test_unready_configuration_cannot_interrupt_supervisor(
    monkeypatch, tmp_path, error
):
    def fail(path):
        raise error

    monkeypatch.setattr(import_alerts, "read_arr_api_key_from_config_xml", fail)
    assert import_alerts.blocked_download_lines(configuration(tmp_path)) == []


def test_missing_api_key_is_a_configuration_error(monkeypatch):
    import runtime_environment
    from xml.etree.ElementTree import Element, ElementTree

    monkeypatch.setattr(
        runtime_environment.ElementTree,
        "parse",
        lambda path: ElementTree(Element("Config")),
    )
    with pytest.raises(ValueError, match="ApiKey not found"):
        runtime_environment.read_arr_api_key_from_config_xml("config.xml")


def test_process_exit_is_not_swallowed(monkeypatch, tmp_path):
    def exit_process(path):
        raise SystemExit(1)

    monkeypatch.setattr(import_alerts, "read_arr_api_key_from_config_xml", exit_process)
    config = configuration(tmp_path)
    with pytest.raises(SystemExit):
        import_alerts.blocked_download_lines(config)


def test_daily_reminder_and_download_deduplication(monkeypatch, tmp_path):
    stub_queues(monkeypatch)
    calls = []
    monkeypatch.setattr(
        import_alerts,
        "deliver_alert_message_best_effort",
        lambda *args: calls.append(True) or True,
    )
    config = configuration(tmp_path)
    import_alerts.maybe_alert_blocked_imports(config, 100000, False)
    import_alerts.maybe_alert_blocked_imports(config, 186400, False)
    assert len(calls) == 2
