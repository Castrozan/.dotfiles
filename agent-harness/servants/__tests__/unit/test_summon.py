import os
import subprocess
import sys
import tempfile
from pathlib import Path

import summon

SERVANTS_DOMAIN_DIRECTORY = Path(summon.__file__).resolve().parent


def _run_summoner_as_the_wrapper_does(base_prompt_path, tmp_path, *launch_arguments):
    """Invoke summon.py the way interactive-sessions.nix does: a bare subprocess
    against the domain directory, with no PYTHONPATH help."""
    completed = subprocess.run(
        [
            sys.executable,
            str(SERVANTS_DOMAIN_DIRECTORY / "summon.py"),
            str(base_prompt_path),
            *launch_arguments,
        ],
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ["PATH"],
            "TMPDIR": str(tmp_path),
            "HOME": str(tmp_path),
        },
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return dict(line.split("=", 1) for line in completed.stdout.strip().splitlines())


class TestTheSummonerRunsStandalone:
    def test_it_composes_a_prompt_from_the_domain_directory(self, tmp_path):
        base_prompt_path = tmp_path / "base.md"
        base_prompt_path.write_text("<interactive>base rules</interactive>\n")

        exports = _run_summoner_as_the_wrapper_does(base_prompt_path, tmp_path)
        composed_text = Path(
            exports["SERVANT_SYSTEM_PROMPT_FILE"].strip("'")
        ).read_text()
        assert "<interactive>base rules</interactive>" in composed_text
        assert "<servant>You are " in composed_text

    def test_it_keeps_one_servant_across_a_resume(self, tmp_path):
        base_prompt_path = tmp_path / "base.md"
        base_prompt_path.write_text("rules\n")

        launched = _run_summoner_as_the_wrapper_does(base_prompt_path, tmp_path)
        minted_session_id = launched["SERVANT_SESSION_ID"].strip("'")
        assert minted_session_id

        resumed = _run_summoner_as_the_wrapper_does(
            base_prompt_path, tmp_path, "--resume", minted_session_id
        )
        assert resumed["SERVANT_NAME"] == launched["SERVANT_NAME"]
        assert resumed["SERVANT_SESSION_ID"] == "''"


class TestServantSystemPromptLine:
    def test_the_prompt_line_names_the_servant_and_bounds_the_flavour(self):
        line = summon.servant_system_prompt_line(
            {"name": "Iskandar", "personality": "King of Conquerors, boisterous."}
        )
        assert line.startswith("<servant>")
        assert line.endswith("</servant>")
        assert "You are Iskandar." in line
        assert "King of Conquerors, boisterous." in line
        assert "never changes your technical accuracy" in line

    def test_composed_file_keeps_the_base_prompt_and_appends_the_servant(
        self, tmp_path, monkeypatch
    ):
        # tempfile caches the resolved directory on first use, and the summoner
        # is a fresh process per launch, so a test that moves TMPDIR mid-process
        # has to clear that cache the way a new process would.
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        monkeypatch.setattr(tempfile, "tempdir", None)
        base_prompt_path = tmp_path / "base.md"
        base_prompt_path.write_text("<interactive>base rules</interactive>\n")

        composed_path = summon.compose_system_prompt_file(
            base_prompt_path, {"name": "Medea", "personality": "Witch of Betrayal."}
        )
        composed_text = composed_path.read_text()
        assert composed_path.parent == tmp_path
        assert "<interactive>base rules</interactive>" in composed_text
        assert "You are Medea." in composed_text


class TestSessionDisplayName:
    def test_session_name_keeps_the_workspace_and_appends_the_servant(
        self, tmp_path, monkeypatch
    ):
        workspace = tmp_path / "ai-first-dev-plataforma"
        workspace.mkdir()
        monkeypatch.chdir(workspace)
        display_name = summon.session_display_name({"name": "Iskandar"}, [])
        assert display_name == "ai-first-dev-plataforma ⋅ Iskandar"

    def test_a_name_the_human_passed_wins_over_the_servant(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        for human_flag in ("-n", "--name"):
            assert (
                summon.session_display_name(
                    {"name": "Iskandar"}, [human_flag, "my-own-name"]
                )
                == ""
            )


class TestShellExports:
    def test_shell_exports_quote_a_servant_name_with_spaces(self, tmp_path):
        exports = summon.shell_export_lines(
            {"name": "Nero Claudius", "personality": "Umu."},
            tmp_path / "composed.md",
        )
        assert "SERVANT_NAME='Nero Claudius'" in exports
        assert any(line.startswith("SERVANT_SYSTEM_PROMPT_FILE=") for line in exports)

    def test_the_personality_is_never_exported_to_the_environment(self, tmp_path):
        exports = summon.shell_export_lines(
            {"name": "Medea", "personality": "Wary."}, tmp_path / "composed.md"
        )
        assert not any("Wary." in export_line for export_line in exports)

    def test_a_minted_session_id_is_exported_for_the_wrapper_to_pass_on(self, tmp_path):
        exports = summon.shell_export_lines(
            {"name": "Medea", "personality": "Wary."},
            tmp_path / "composed.md",
            "",
            "2295054f-355a-4182-9d8d-140f9714e062",
        )
        assert "SERVANT_SESSION_ID=2295054f-355a-4182-9d8d-140f9714e062" in exports

    def test_an_unminted_launch_exports_an_empty_session_id(self, tmp_path):
        exports = summon.shell_export_lines(
            {"name": "Medea", "personality": "Wary."}, tmp_path / "composed.md"
        )
        assert "SERVANT_SESSION_ID=''" in exports
