import json
import logging
import os

from playback import player_diagnostics as diagnostics


def test_report_replacement_is_readable_and_has_no_leftover_temporary_file(tmp_path):
    diagnostics.write_player_report(tmp_path, {"status": "running"})
    diagnostics.write_player_report(tmp_path, {"status": "failed", "exit_code": 12})
    assert json.loads((tmp_path / "report.json").read_text()) == {
        "status": "failed",
        "exit_code": 12,
    }
    assert list(tmp_path.iterdir()) == [tmp_path / "report.json"]


def test_completed_run_retention_preserves_incomplete_runs(tmp_path):
    for index in range(12):
        run_directory = tmp_path / "player-runs" / f"20260928-{index:02}"
        run_directory.mkdir(parents=True)
        diagnostics.write_player_report(run_directory, {"status": "exited"})
        (run_directory / "player.log").write_text("old output")
    active_directory = tmp_path / "player-runs" / "20260927-active"
    active_directory.mkdir()
    diagnostics.write_player_report(
        active_directory, {"status": "running", "supervisor_pid": os.getpid()}
    )
    run_directory = diagnostics.create_player_run(tmp_path)
    assert run_directory.is_dir()
    assert active_directory.is_dir()
    assert not (tmp_path / "player-runs" / "20260928-00").exists()
    assert len(list((tmp_path / "player-runs").iterdir())) == 12


def test_logger_records_lifecycle_messages_on_disk(tmp_path):
    logger = diagnostics.create_diagnostic_logger(
        "test.canvas", tmp_path / "launcher.log"
    )
    logger.info("launcher_check player_running=%s", False)
    for handler in logger.handlers:
        handler.close()
    log = (tmp_path / "launcher.log").read_text()
    assert "INFO launcher_check player_running=False" in log
    assert not logger.propagate
    logging.getLogger("test.canvas").handlers.clear()
