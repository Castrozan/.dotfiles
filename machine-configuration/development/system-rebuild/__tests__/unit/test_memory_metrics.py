import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/nixos-staged-rebuild"


@pytest.fixture
def metrics(monkeypatch):
    monkeypatch.syspath_prepend(SCRIPTS)
    return importlib.import_module("memory_records")


@pytest.mark.parametrize("exit_status", [0, 42])
def test_recorded_command_keeps_output_resources_and_exit_status(
    monkeypatch, tmp_path, exit_status
):
    monkeypatch.syspath_prepend(SCRIPTS)
    command = importlib.import_module("staged_command")
    records = tmp_path / "records"
    monkeypatch.setenv("REBUILD_MEMORY_RECORDS", str(records))
    monkeypatch.setenv("REBUILD_COMMAND_TIME", shutil.which("time"))
    arguments = [
        sys.executable,
        "-c",
        f"print('captured'); raise SystemExit({exit_status})",
    ]
    if exit_status:
        with pytest.raises(subprocess.CalledProcessError) as failure:
            command.run_command("evaluation", arguments, True)
        assert failure.value.returncode == exit_status
        assert failure.value.output == "captured\n"
    else:
        assert command.run_command("evaluation", arguments, True) == "captured"
    record = json.loads(records.read_text())
    assert record["exit_status"] == exit_status
    assert record["peak_rss_kib"] > 0
    assert record["wall_seconds"] >= 0


def test_report_preserves_units_scope_sources_and_component_details(metrics):
    records = [
        {"sources": {"public": "git+file:///source?rev=immutable"}},
        {"phase": "evaluation", "peak_rss_kib": 2048, "wall_seconds": 2},
        {"phase": "component_devenv", "peak_rss_kib": 1024, "wall_seconds": 1},
        {"component": "component_devenv", "output_count": 1, "reference": "source"},
    ]
    report = metrics.create_report(
        records, metrics.RebuildRun("switch", "chise", "start", 42)
    )
    assert report["exit_status"] == 42
    assert report["started_at"] == "start"
    assert report["sources"] == records[0]["sources"]
    assert report["phases"][0]["peak_rss_mib"] == 2
    assert report["components"][0]["peak_rss_mib"] == 1
    assert report["components"][0]["output_count"] == 1
    assert "must not be added" in report["scope"]
    assert "daemon workers" in report["scope"]


def test_normal_run_keeps_the_last_explicit_component_report(metrics, tmp_path):
    records = tmp_path / "records"
    directory = tmp_path / "metrics"
    records.write_text(
        json.dumps({"phase": "component_devenv", "peak_rss_kib": 1024}) + "\n"
    )
    metrics.publish_report(
        records, directory, metrics.RebuildRun("switch", "chise", "first", 0)
    )
    component_report = (directory / "latest-components.json").read_bytes()
    records.write_text(json.dumps({"phase": "evaluation", "peak_rss_kib": 2048}))
    metrics.publish_report(
        records, directory, metrics.RebuildRun("switch", "chise", "second", 0)
    )
    assert (directory / "latest-components.json").read_bytes() == component_report
    report = json.loads((directory / "latest.json").read_text())
    assert report["started_at"] == "second"
    assert not report["components"]
    assert len(list(directory.iterdir())) == 2


@pytest.mark.parametrize("exit_status,content", [(99, "invalid"), (0, "")])
def test_contended_or_empty_run_does_not_replace_metrics(
    metrics, tmp_path, exit_status, content
):
    records = tmp_path / "records"
    records.write_text(content)
    destination = tmp_path / "latest.json"
    destination.write_text("previous")
    metrics.publish_report(
        records, tmp_path, metrics.RebuildRun("switch", "chise", "now", exit_status)
    )
    assert destination.read_text() == "previous"


def test_record_write_error_does_not_mask_command_result(
    metrics, monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv("REBUILD_MEMORY_RECORDS", str(tmp_path))
    metrics.append_record({"phase": "activation"})
    assert "cannot record rebuild memory metrics" in capsys.readouterr().err
