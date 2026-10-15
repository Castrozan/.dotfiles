import pytest

from import_repair import maintenance, repair
import import_repair.redundant_downloads.cleanup as cleanup


def test_active_manual_import_preserves_pack(completed_pack, run_cleanup):
    completed_pack[4]["commands"] = [{"name": "ManualImport", "status": "started"}]
    removed, calls = run_cleanup()
    assert not removed
    assert len(calls) == 1


def test_failed_native_removal_is_not_reported_as_success(run_cleanup):
    with pytest.raises(ValueError, match="removal returned HTTP 503"):
        run_cleanup(delete_status=503)


def test_cleanup_runs_before_import_repair_and_respects_disk_guard(monkeypatch):
    calls = []
    monkeypatch.setattr(
        maintenance,
        "maybe_cleanup_redundant_downloads",
        lambda *args: calls.append("cleanup"),
    )
    monkeypatch.setattr(
        maintenance,
        "maybe_repair_blocked_imports",
        lambda *args: calls.append("repair"),
    )
    maintain = lambda: maintenance.maintain_blocked_imports({}, 1000, False)
    repair.maybe_repair_if_unblocked(["qbittorrent"], maintain)
    assert calls == []
    repair.maybe_repair_if_unblocked([], maintain)
    assert calls == ["cleanup", "repair"]


@pytest.mark.parametrize("failure", [OSError, ValueError, KeyError, TypeError])
def test_failed_verification_does_not_block_other_downloads(
    monkeypatch, completed_pack, failure
):
    record = completed_pack[0]
    records = [record, dict(record, downloadId="b" * 40)]
    monkeypatch.setattr(cleanup, "read_arr_api_key_from_config_xml", lambda path: "key")
    monkeypatch.setattr(cleanup, "queued_records", lambda *args: records)
    calls = []

    def remove(base, key, value, dry_run):
        calls.append(value["downloadId"])
        raise failure("Sonarr unavailable")

    monkeypatch.setattr(cleanup, "remove_redundant_download", remove)
    cleanup.maybe_cleanup_redundant_downloads(
        {"sonarr_url": "url", "sonarr_config_file": "xml"}, 0, False
    )
    assert calls == ["a" * 40, "b" * 40]


def test_bounded_sweep_rotates_past_unresolvable_packs(monkeypatch, completed_pack):
    records = [
        dict(completed_pack[0], downloadId=f"{number:040x}") for number in range(5)
    ]
    monkeypatch.setattr(cleanup, "read_arr_api_key_from_config_xml", lambda path: "key")
    monkeypatch.setattr(cleanup, "queued_records", lambda *args: records)
    selected = []
    monkeypatch.setattr(
        cleanup,
        "remove_redundant_download",
        lambda base, key, value, dry: selected.append(value["downloadId"]) or False,
    )
    for now_epoch in (0, 60, 120):
        cleanup.maybe_cleanup_redundant_downloads(
            {"sonarr_url": "url", "sonarr_config_file": "xml"}, now_epoch, False
        )
    assert len(selected) == 6
    assert len(set(selected)) == 5
