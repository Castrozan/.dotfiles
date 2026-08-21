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

    def test_it_prints_the_name_alone_so_a_caller_can_use_it_verbatim(self, capsys):
        servant_name.main(["servant-name", "verbatim-probe"])
        printed = capsys.readouterr().out
        assert printed.count("\n") == 1
        assert "|" not in printed
        assert " - " not in printed


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

    def test_the_script_resolves_its_catalog_without_help(self):
        completed = self._run("subprocess-probe")
        assert completed.returncode == 0, completed.stderr
        assert (
            completed.stdout.strip()
            == catalog.select_servant_for_session("subprocess-probe")["name"]
        )

    def test_the_statusline_and_the_session_agree_on_the_same_id(self):
        """The two surfaces derive the name independently, so a session sees the
        name its statusline shows only while both draws stay identical."""
        session_id = "9f1c2d3e-agreement-probe"
        assert (
            self._run(session_id).stdout.strip()
            == catalog.select_servant_for_session(session_id)["name"]
        )
