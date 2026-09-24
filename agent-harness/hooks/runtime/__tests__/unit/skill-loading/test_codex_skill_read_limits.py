import record_codex_skill_read_handler
import skill_loaded_marker


def test_non_cat_commands_do_not_read_skill_files(monkeypatch, tmp_path):
    def unexpected_open(*arguments, **keywords):
        raise AssertionError("Unrelated commands must not read skill files")

    monkeypatch.setattr(record_codex_skill_read_handler.Path, "open", unexpected_open)
    assert (
        record_codex_skill_read_handler.handle(
            {
                "session_id": "bounded-read",
                "cwd": str(tmp_path),
                "tool_input": {"command": "git status"},
                "tool_response": "clean",
            }
        )
        is None
    )


def test_cat_parser_rejects_oversized_and_malformed_commands(tmp_path):
    commands = (
        "cat " + "x" * record_codex_skill_read_handler.MAXIMUM_COMMAND_CHARACTERS,
        "cat " + " ".join(f"path-{index}" for index in range(17)),
        'cat "unterminated',
        "cat",
        None,
    )
    for command in commands:
        assert (
            record_codex_skill_read_handler.standalone_cat_paths(
                {"command": command}, str(tmp_path)
            )
            == set()
        )


def test_skill_read_size_is_bounded(monkeypatch, tmp_path):
    monkeypatch.setattr(record_codex_skill_read_handler.Path, "home", lambda: tmp_path)
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))
    path = (
        tmp_path
        / ".local/share/agent-plugins/dotfiles/plugin/skills/instructions/SKILL.md"
    )
    path.parent.mkdir(parents=True)
    content = "x" * (record_codex_skill_read_handler.MAXIMUM_SKILL_BYTES + 1)
    path.write_text(content)
    record_codex_skill_read_handler.handle(
        {
            "session_id": "bounded-read",
            "cwd": str(tmp_path),
            "tool_input": {"command": f"cat {path}"},
            "tool_response": content,
        }
    )
    assert not skill_loaded_marker.has_skill_loaded("instructions", "bounded-read")
