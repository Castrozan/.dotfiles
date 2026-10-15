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

    def maintain():
        maintenance.maintain_blocked_imports({}, 1000, False)

    repair.maybe_repair_if_unblocked(["qbittorrent"], maintain)
    assert calls == []
    repair.maybe_repair_if_unblocked([], maintain)
    assert calls == ["cleanup", "repair"]


@pytest.mark.parametrize("failure", [OSError, ValueError, KeyError, TypeError])
def test_failed_verification_does_not_block_other_downloads(
    monkeypatch, completed_pack, tmp_path, failure
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
        {
            "sonarr_url": "url",
            "sonarr_config_file": "xml",
            "state_file_path": str(tmp_path / "last-active"),
        },
        False,
    )
    assert calls == ["a" * 40, "b" * 40]


@pytest.mark.parametrize("queue_count", [3, 5, 6])
@pytest.mark.parametrize("poll_seconds", [60, 180])
def test_bounded_sweep_rotates_past_unresolvable_packs(
    monkeypatch, completed_pack, tmp_path, queue_count, poll_seconds
):
    records = [
        dict(completed_pack[0], downloadId=f"{number:040x}")
        for number in range(queue_count)
    ]
    monkeypatch.setattr(cleanup, "read_arr_api_key_from_config_xml", lambda path: "key")
    monkeypatch.setattr(cleanup, "queued_records", lambda *args: records)
    selected = []
    monkeypatch.setattr(
        cleanup,
        "remove_redundant_download",
        lambda base, key, value, dry: selected.append(value["downloadId"]) or False,
    )
    attempts = (queue_count + 1) // 2
    monkeypatch.setattr(maintenance, "maybe_repair_blocked_imports", lambda *args: None)
    for now_epoch in range(0, poll_seconds * attempts, poll_seconds):
        maintenance.maintain_blocked_imports(
            {
                "sonarr_url": "url",
                "sonarr_config_file": "xml",
                "state_file_path": str(tmp_path / "last-active"),
            },
            now_epoch,
            False,
        )
    assert len(selected) == 2 * attempts
    assert len(set(selected)) == queue_count
