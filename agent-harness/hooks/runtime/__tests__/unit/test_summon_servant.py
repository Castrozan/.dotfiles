import summon_servant


class TestServantSystemPromptLine:
    def test_the_prompt_line_names_the_servant_and_bounds_the_flavour(self):
        line = summon_servant.servant_system_prompt_line(
            {"name": "Iskandar", "manner": "King of Conquerors, boisterous."}
        )
        assert line.startswith("<servant>")
        assert line.endswith("</servant>")
        assert "You are Iskandar." in line
        assert "King of Conquerors, boisterous." in line
        assert "never changes your technical accuracy" in line

    def test_composed_file_keeps_the_base_prompt_and_appends_the_servant(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        base_prompt_path = tmp_path / "base.md"
        base_prompt_path.write_text("<interactive>base rules</interactive>\n")

        composed_path = summon_servant.compose_system_prompt_file(
            base_prompt_path, {"name": "Medea", "manner": "Witch of Betrayal."}
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
        display_name = summon_servant.session_display_name({"name": "Iskandar"}, [])
        assert display_name == "ai-first-dev-plataforma ⋅ Iskandar"

    def test_a_name_the_human_passed_wins_over_the_servant(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        for human_flag in ("-n", "--name"):
            assert (
                summon_servant.session_display_name(
                    {"name": "Iskandar"}, [human_flag, "my-own-name"]
                )
                == ""
            )


class TestShellExports:
    def test_shell_exports_quote_a_servant_name_with_spaces(self, tmp_path):
        exports = summon_servant.shell_export_lines(
            {"name": "Nero Claudius", "class": "Saber", "manner": "Umu."},
            tmp_path / "composed.md",
        )
        assert "SERVANT_NAME='Nero Claudius'" in exports
        assert any(line.startswith("SERVANT_SYSTEM_PROMPT_FILE=") for line in exports)
