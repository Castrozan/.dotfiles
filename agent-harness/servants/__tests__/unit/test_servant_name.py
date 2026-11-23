import subprocess
import sys
from pathlib import Path

import catalog
import servant_name

SERVANT_NAME_SCRIPT = Path(servant_name.__file__)


class TestPrintingTheName:
    def test_it_prints_the_name_the_session_was_drawn(self, capsys):
        exit_code = servant_name.main(["servant-name", "statusline-probe"])
        printed = capsys.readouterr().out.strip()
        assert exit_code == 0
        assert printed == catalog.select_servant_for_session("statusline-probe")["name"]


class TestNoSessionId:
    """Every id-less caller would otherwise be handed the same Servant, which is
    worse than a statusline segment that simply does not appear."""

    def test_a_missing_id_prints_nothing_and_fails(self, capsys):
        assert servant_name.main(["servant-name"]) == 1
        assert capsys.readouterr().out == ""

    def test_an_empty_id_prints_nothing_and_fails(self, capsys):
        assert servant_name.main(["servant-name", ""]) == 1
        assert capsys.readouterr().out == ""


class TestRunningAsItsOwnProcess:
    """The packaged command execs this file directly with no PYTHONPATH, so the
    sibling import has to resolve off the script's own directory."""

    def _run(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SERVANT_NAME_SCRIPT), *arguments],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
        )
