import subprocess

from directory_entry_guard_handler import handle


def test_excluded_repository_pattern_skips_limit(
    repository_at_entry_limit, tmp_path, monkeypatch
):
    patterns_file = tmp_path / "excluded-repositories.txt"
    patterns_file.write_text(
        f"# excluded roots\n{tmp_path}/repo*\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DIRECTORY_ENTRY_EXCLUDED_REPOSITORIES_FILE", str(patterns_file))
    assert (
        handle(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(repository_at_entry_limit / "source/file15.py")
                },
            }
        )
        is None
    )


def test_repository_outside_excluded_patterns_still_denies(
    repository_at_entry_limit, tmp_path, monkeypatch
):
    patterns_file = tmp_path / "excluded-repositories.txt"
    patterns_file.write_text("/nowhere/*\n", encoding="utf-8")
    monkeypatch.setenv("DIRECTORY_ENTRY_EXCLUDED_REPOSITORIES_FILE", str(patterns_file))
    result = handle(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(repository_at_entry_limit / "source/file15.py")
            },
        }
    )
    assert result.decision == "deny"


def test_missing_excluded_repositories_file_enforces_limit(
    repository_at_entry_limit, monkeypatch
):
    monkeypatch.setenv(
        "DIRECTORY_ENTRY_EXCLUDED_REPOSITORIES_FILE", "/nonexistent/excluded.txt"
    )
    result = handle(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(repository_at_entry_limit / "source/file15.py")
            },
        }
    )
    assert result.decision == "deny"


def test_origin_remote_pattern_excludes_repository(
    repository_at_entry_limit, tmp_path, monkeypatch
):
    subprocess.run(
        [
            "git",
            "-C",
            str(repository_at_entry_limit),
            "remote",
            "add",
            "origin",
            "git@gitlab.example.com:group/project.git",
        ],
        check=True,
    )
    patterns_file = tmp_path / "excluded-repositories.txt"
    patterns_file.write_text("*gitlab.example.com*\n", encoding="utf-8")
    monkeypatch.setenv("DIRECTORY_ENTRY_EXCLUDED_REPOSITORIES_FILE", str(patterns_file))
    assert (
        handle(
            {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(repository_at_entry_limit / "source/file15.py")
                },
            }
        )
        is None
    )
