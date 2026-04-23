import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "launch-claude-workspace-session"
)
script_loader = importlib.machinery.SourceFileLoader(
    "launch_claude_workspace_session", str(SCRIPT_PATH)
)
module_specification = importlib.util.spec_from_loader(
    "launch_claude_workspace_session", script_loader
)
loaded_workspace_launcher_module = importlib.util.module_from_spec(module_specification)
module_specification.loader.exec_module(loaded_workspace_launcher_module)


def test_prepare_workspace_claude_launch_plan_only_links_minimal_runtime_entries(
    tmp_path,
):
    global_claude_config_directory = tmp_path / "global-claude"
    global_claude_config_directory.mkdir()
    (global_claude_config_directory / ".credentials.json").write_text("{}\n")
    (global_claude_config_directory / "settings.json").write_text("{}\n")
    (global_claude_config_directory / "keybindings.json").write_text("{}\n")
    (global_claude_config_directory / "plugins").mkdir()
    (global_claude_config_directory / "rules").mkdir()
    (global_claude_config_directory / "history.jsonl").write_text("history\n")
    (global_claude_config_directory / "skills").mkdir()

    workspace_directory = tmp_path / "workspace"
    alpha_skill_directory = workspace_directory / "alpha"
    beta_skill_directory = workspace_directory / "nested" / "beta"
    beta_skill_directory.mkdir(parents=True)
    alpha_skill_directory.mkdir(parents=True)
    (alpha_skill_directory / "SKILL.md").write_text("---\nname: alpha\n---\n")
    (beta_skill_directory / "SKILL.md").write_text("---\nname: beta\n---\n")

    global_claude_state_file = tmp_path / ".claude.json"
    global_claude_state_file.write_text('{"installMethod":"native"}\n')
    core_instructions_file = tmp_path / "core.md"
    core_instructions_file.write_text(
        "---\ndescription: core\n---\n\n<user>\nCore body.\n</user>\n"
    )

    launch_plan = loaded_workspace_launcher_module.prepare_workspace_claude_launch_plan(
        temporary_workspace_directory=tmp_path / "temporary-workspace",
        global_claude_config_directory=global_claude_config_directory,
        global_claude_state_file=global_claude_state_file,
        core_instructions_file=core_instructions_file,
        personal_skill_set_directory=tmp_path / "personal-skills",
        extend_workspace_with_global_skills=False,
        requested_skill_source_directories=[],
        workspace_search_root_directory=workspace_directory,
        claude_binary_path="/bin/claude",
    )

    workspace_config_directory = launch_plan.config_directory

    assert (workspace_config_directory / ".credentials.json").is_symlink()
    assert (workspace_config_directory / "settings.json").is_symlink()
    assert (workspace_config_directory / "keybindings.json").is_symlink()
    assert (workspace_config_directory / "plugins").is_symlink()
    assert not (workspace_config_directory / "rules").exists()
    assert not (workspace_config_directory / "history.jsonl").exists()
    assert (workspace_config_directory / ".claude.json").is_symlink()
    assert (
        workspace_config_directory / "skills" / "alpha"
    ).resolve() == alpha_skill_directory.resolve()
    assert (
        workspace_config_directory / "skills" / "beta"
    ).resolve() == beta_skill_directory.resolve()
    assert launch_plan.loaded_skill_names == ["alpha", "beta"]
    assert launch_plan.command_arguments == ["/bin/claude"]
    assert (
        workspace_config_directory / "CLAUDE.md"
    ).read_text() == "\n<user>\nCore body.\n</user>\n"


def test_prepare_workspace_claude_launch_plan_merges_global_skills_only_with_extend(
    tmp_path,
):
    global_claude_config_directory = tmp_path / "global-claude"
    (global_claude_config_directory / "skills" / "shared").mkdir(parents=True)
    (global_claude_config_directory / "skills" / "shared" / "SKILL.md").write_text(
        "---\nname: shared\n---\n"
    )
    (global_claude_config_directory / "skills" / "local").mkdir(parents=True)
    (global_claude_config_directory / "skills" / "local" / "SKILL.md").write_text(
        "---\nname: local-global\n---\n"
    )

    workspace_directory = tmp_path / "workspace"
    local_skill_directory = workspace_directory / "local"
    local_skill_directory.mkdir(parents=True)
    (local_skill_directory / "SKILL.md").write_text("---\nname: local\n---\n")

    launch_plan = loaded_workspace_launcher_module.prepare_workspace_claude_launch_plan(
        temporary_workspace_directory=tmp_path / "temporary-workspace",
        global_claude_config_directory=global_claude_config_directory,
        global_claude_state_file=tmp_path / "missing-claude-state.json",
        core_instructions_file=tmp_path / "core.md",
        personal_skill_set_directory=tmp_path / "personal-skill-set",
        extend_workspace_with_global_skills=True,
        requested_skill_source_directories=[],
        workspace_search_root_directory=workspace_directory,
        claude_binary_path="/bin/claude",
    )

    assert (
        launch_plan.config_directory / "skills" / "local"
    ).resolve() == local_skill_directory.resolve()
    assert (launch_plan.config_directory / "skills" / "shared").exists()
    assert launch_plan.loaded_skill_names == ["local", "shared"]
    assert launch_plan.command_arguments == [
        "/bin/claude",
        "--add-dir",
        str((tmp_path / "personal-skill-set").resolve()),
    ]


def test_prepare_workspace_claude_launch_plan_rejects_empty_workspace_without_extend(
    tmp_path,
):
    with pytest.raises(
        loaded_workspace_launcher_module.WorkspaceLaunchConfigurationError
    ):
        loaded_workspace_launcher_module.prepare_workspace_claude_launch_plan(
            temporary_workspace_directory=tmp_path / "temporary-workspace",
            global_claude_config_directory=tmp_path / "global-claude",
            global_claude_state_file=tmp_path / "missing-claude-state.json",
            core_instructions_file=tmp_path / "core.md",
            personal_skill_set_directory=tmp_path / "personal-skill-set",
            extend_workspace_with_global_skills=False,
            requested_skill_source_directories=[],
            workspace_search_root_directory=tmp_path / "workspace",
            claude_binary_path="/bin/claude",
        )


def test_resolve_requested_skill_source_directories_requires_skill_markdown(tmp_path):
    missing_skill_markdown_directory = tmp_path / "without-skill-markdown"
    missing_skill_markdown_directory.mkdir()

    with pytest.raises(
        loaded_workspace_launcher_module.WorkspaceLaunchConfigurationError
    ):
        loaded_workspace_launcher_module.resolve_requested_skill_source_directories(
            [str(missing_skill_markdown_directory)]
        )
