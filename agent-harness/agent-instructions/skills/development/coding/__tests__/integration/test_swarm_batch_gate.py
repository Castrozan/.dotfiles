import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent.parent / "scripts"
BATCH_GATE_SCRIPT = SCRIPTS_DIRECTORY / "swarm-batch-gate.py"


def run_script(script, *arguments, working_directory):
    return subprocess.run(
        [sys.executable, str(script), *arguments],
        capture_output=True,
        text=True,
        cwd=working_directory,
        timeout=120,
    )


def test_batch_gate_reports_each_batch_and_fails_when_one_batch_fails(tmp_path):
    (tmp_path / "clean one.py").write_text("value = 1\n")
    (tmp_path / "clean_two.py").write_text("value = 2\n")
    (tmp_path / "broken.py").write_text("BROKEN\n")
    batches_path = tmp_path / "batches.json"
    batches_path.write_text(
        json.dumps({"good": ["clean one.py", "clean_two.py"], "bad": ["broken.py"]})
    )
    result = run_script(
        BATCH_GATE_SCRIPT,
        "--batches",
        str(batches_path),
        "--check",
        "! grep -l BROKEN {files}",
        working_directory=tmp_path,
    )
    assert result.returncode == 1
    assert "PASS  good" in result.stdout
    assert "FAIL  bad" in result.stdout
    assert "broken.py" in result.stdout
    assert "1 of 2 batch checks passed" in result.stdout


def test_batch_gate_passes_when_every_check_passes_for_every_batch(tmp_path):
    (tmp_path / "module.py").write_text("value = 1\n")
    batches_path = tmp_path / "batches.json"
    batches_path.write_text(json.dumps({"only": ["module.py"]}))
    result = run_script(
        BATCH_GATE_SCRIPT,
        "--batches",
        str(batches_path),
        "--check",
        "test -s {files}",
        "--check",
        "! grep -l BROKEN {files}",
        working_directory=tmp_path,
    )
    assert result.returncode == 0
    assert "2 of 2 batch checks passed" in result.stdout


def test_batch_gate_rejects_a_batch_that_is_not_a_file_list(tmp_path):
    batches_path = tmp_path / "batches.json"
    batches_path.write_text(json.dumps({"single": "module.py"}))
    result = run_script(
        BATCH_GATE_SCRIPT,
        "--batches",
        str(batches_path),
        "--check",
        "true {files}",
        working_directory=tmp_path,
    )
    assert result.returncode != 0
    assert "must hold" in result.stderr
