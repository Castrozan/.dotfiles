import os
import subprocess
import sys
from pathlib import Path

import pytest

RANKER = (
    Path(__file__).resolve().parents[2]
    / "scripts/command-launcher/command-history-ranker.py"
)


@pytest.mark.parametrize("exit_status", [0, 6])
def test_ranker_preserves_history_records_and_backend_status(tmp_path, exit_status):
    history = tmp_path / "history"
    original_history = "vt_prod\nvt_test\n#1790965010\nprintf '%s' 'first\nsecond'\n"
    history.write_text(original_history)
    captured_history = tmp_path / "captured-history"
    captured_arguments = tmp_path / "captured-arguments"
    backend = tmp_path / "backend"
    backend.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        "assert (Path(os.environ['HOME']) / '.hstr_blacklist').read_text() == ''\n"
        "assert os.environ['HSTR_CONFIG'] == 'keywords-matching,blacklist'\n"
        f"Path({str(captured_history)!r}).write_bytes(Path(os.environ['HISTFILE']).read_bytes())\n"
        f"Path({str(captured_arguments)!r}).write_text('\\n'.join(sys.argv[1:]))\n"
        "sys.stdout.buffer.write(b'vt_test\\0')\n"
        f"sys.exit({exit_status})\n"
    )
    backend.chmod(0o755)
    result = subprocess.run(
        [sys.executable, str(RANKER), str(backend), "--non-interactive", "vt", "test"],
        env=os.environ | {"HISTFILE": str(history)},
        capture_output=True,
        check=False,
    )
    assert result.returncode == exit_status
    assert result.stdout == b"vt_test\0"
    assert history.read_text() == original_history
    assert captured_history.read_text() == (
        "#0\nvt_prod\n#0\nvt_test\n#1790965010\nprintf '%s' 'first\nsecond'\n"
    )
    assert captured_arguments.read_text().splitlines() == [
        "--non-interactive",
        "vt",
        "test",
    ]


def test_unreadable_history_does_not_start_the_backend(tmp_path):
    result = subprocess.run(
        [sys.executable, str(RANKER), "/missing-backend", "--non-interactive", "vt"],
        env=os.environ | {"HISTFILE": str(tmp_path / "missing-history")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "cannot read command history" in result.stderr
