import sys
from datetime import datetime, timezone
from pathlib import Path

PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY))

import performance_log_archiver

SAMPLE_TIMESTAMP = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)


def test_should_archive_today_true_when_no_marker(tmp_path):
    assert performance_log_archiver.should_archive_today(tmp_path, "2026-07-11") is True


def test_should_archive_today_reflects_marker_date(tmp_path):
    performance_log_archiver.last_archive_date_marker_path(tmp_path).write_text(
        "2026-07-11", encoding="utf-8"
    )
    assert (
        performance_log_archiver.should_archive_today(tmp_path, "2026-07-11") is False
    )
    assert performance_log_archiver.should_archive_today(tmp_path, "2026-07-12") is True


def test_archive_tmp_logs_writes_marker_and_copies_present_sources(
    tmp_path, monkeypatch
):
    source_log_path = tmp_path / "example-source.log"
    source_log_path.write_text("switcher line\n", encoding="utf-8")
    monkeypatch.setattr(
        performance_log_archiver, "ARCHIVED_TMP_LOG_PATHS", [source_log_path]
    )

    state_directory = tmp_path / "state"
    archived_paths = performance_log_archiver.archive_tmp_logs(
        state_directory, SAMPLE_TIMESTAMP, retained_months=6
    )

    marker_text = performance_log_archiver.last_archive_date_marker_path(
        state_directory
    ).read_text(encoding="utf-8")
    assert marker_text == "2026-07-11"
    assert len(archived_paths) == 1
    assert archived_paths[0].name == "example-source-2026-07-11.log"
    assert archived_paths[0].read_text(encoding="utf-8") == "switcher line\n"


def test_prune_archived_logs_older_than_removes_stale_dated_copies(tmp_path):
    archive_directory = tmp_path / "archived-logs"
    archive_directory.mkdir(parents=True)
    for dated_name in (
        "workspace-switcher-perf-2026-07-11.log",
        "workspace-switcher-perf-2026-02-01.log",
        "karabiner-daemon-2025-12-31.log",
    ):
        (archive_directory / dated_name).write_text("x\n", encoding="utf-8")

    removed = performance_log_archiver.prune_archived_logs_older_than(
        tmp_path, SAMPLE_TIMESTAMP, retained_months=6
    )

    surviving_names = {path.name for path in archive_directory.iterdir()}
    assert surviving_names == {
        "workspace-switcher-perf-2026-07-11.log",
        "workspace-switcher-perf-2026-02-01.log",
    }
    assert {path.name for path in removed} == {"karabiner-daemon-2025-12-31.log"}
