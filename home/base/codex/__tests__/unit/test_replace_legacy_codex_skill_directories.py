import os
import subprocess
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "replace-legacy-codex-skill-directories"
)


def run_script(codex_skills_path: Path, bash_environment_path: Path):
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=os.environ
        | {
            "BASH_ENV": str(bash_environment_path),
            "CODEX_SKILLS_PATH": str(codex_skills_path),
            "COREUTILS_BIN": "/bin",
            "GREP_BIN": "/usr/bin/grep",
        },
    )


def test_replaces_a_legacy_generated_skill_directory_when_bash_env_aliases_ls(
    tmp_path,
):
    codex_skills_path = tmp_path / "skills"
    core_skill_directory = codex_skills_path / "core"
    core_skill_directory.mkdir(parents=True)
    legacy_skill_file = tmp_path / "legacy-core-skill.md"
    legacy_skill_file.write_text("---\nname: core\n---\n")
    (core_skill_directory / "SKILL.md").symlink_to(legacy_skill_file)
    bash_environment_path = tmp_path / "aliases.bash"
    bash_environment_path.write_text("alias ls='false'\n")

    result = run_script(codex_skills_path, bash_environment_path)

    assert result.returncode == 0
    assert not core_skill_directory.exists()


def test_preserves_a_pinchtab_directory_that_contains_user_content(tmp_path):
    codex_skills_path = tmp_path / "skills"
    pinchtab_skill_directory = codex_skills_path / "pinchtab"
    pinchtab_skill_directory.mkdir(parents=True)
    legacy_skill_file = tmp_path / "legacy-pinchtab-skill.md"
    legacy_skill_file.write_text("---\nname: pinchtab\n---\n")
    (pinchtab_skill_directory / "SKILL.md").symlink_to(legacy_skill_file)
    (pinchtab_skill_directory / "private-notes.txt").write_text("keep")
    bash_environment_path = tmp_path / "aliases.bash"
    bash_environment_path.write_text("")

    result = run_script(codex_skills_path, bash_environment_path)

    assert result.returncode == 0
    assert (pinchtab_skill_directory / "private-notes.txt").read_text() == "keep"
