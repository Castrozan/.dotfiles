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
    (global_claude_config_directory / "projects").mkdir()
    (global_claude_config_directory / "rules").mkdir()
    (global_claude_config_directory / "history.jsonl").write_text("history\n")
    (global_claude_config_directory / "skills").mkdir()
    (global_claude_config_directory / "skills" / "core").mkdir()
    (global_claude_config_directory / "skills" / "core" / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )
    (global_claude_config_directory / "skills" / "personal-skills").mkdir()
    (
        global_claude_config_directory / "skills" / "personal-skills" / "SKILL.md"
    ).write_text("---\nname: personal-skills\n---\n")

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

    workspace_credentials_file = workspace_config_directory / ".credentials.json"
    assert workspace_credentials_file.is_file()
    assert not workspace_credentials_file.is_symlink()
    assert workspace_credentials_file.read_text() == "{}\n"
    assert (workspace_config_directory / "settings.json").is_symlink()
    assert (workspace_config_directory / "keybindings.json").is_symlink()
    assert (workspace_config_directory / "plugins").is_symlink()
    assert (workspace_config_directory / "projects").is_symlink()
    assert (workspace_config_directory / "history.jsonl").is_symlink()
    assert not (workspace_config_directory / "rules").exists()
    assert (workspace_config_directory / ".claude.json").is_symlink()
    assert (
        workspace_config_directory / "skills" / "alpha"
    ).resolve() == alpha_skill_directory.resolve()
    assert (
        workspace_config_directory / "skills" / "beta"
    ).resolve() == beta_skill_directory.resolve()
    assert (workspace_config_directory / "skills" / "core").exists()
    assert (workspace_config_directory / "skills" / "personal-skills").exists()
    assert launch_plan.loaded_skill_names == [
        "alpha",
        "beta",
        "core",
        "personal-skills",
    ]
    assert launch_plan.command_arguments == ["/bin/claude"]
    assert (
        workspace_config_directory / "CLAUDE.md"
    ).read_text() == "\n<user>\nCore body.\n</user>\n"


def test_prepare_workspace_claude_launch_plan_merges_global_skills_only_with_extend(
    tmp_path,
):
    global_claude_config_directory = tmp_path / "global-claude"
    (global_claude_config_directory / "skills" / "core").mkdir(parents=True)
    (global_claude_config_directory / "skills" / "core" / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )
    (global_claude_config_directory / "skills" / "personal-skills").mkdir(parents=True)
    (
        global_claude_config_directory / "skills" / "personal-skills" / "SKILL.md"
    ).write_text("---\nname: personal-skills\n---\n")
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
    assert launch_plan.loaded_skill_names == [
        "core",
        "local",
        "personal-skills",
        "shared",
    ]
    assert launch_plan.command_arguments == [
        "/bin/claude",
        "--add-dir",
        str((tmp_path / "personal-skill-set").resolve()),
    ]


def test_prepare_workspace_claude_launch_plan_loads_default_skills_for_empty_workspace(
    tmp_path,
):
    global_claude_config_directory = tmp_path / "global-claude"
    (global_claude_config_directory / "skills" / "core").mkdir(parents=True)
    (global_claude_config_directory / "skills" / "core" / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )
    (global_claude_config_directory / "skills" / "personal-skills").mkdir(parents=True)
    (
        global_claude_config_directory / "skills" / "personal-skills" / "SKILL.md"
    ).write_text("---\nname: personal-skills\n---\n")

    launch_plan = loaded_workspace_launcher_module.prepare_workspace_claude_launch_plan(
        temporary_workspace_directory=tmp_path / "temporary-workspace",
        global_claude_config_directory=global_claude_config_directory,
        global_claude_state_file=tmp_path / "missing-claude-state.json",
        core_instructions_file=tmp_path / "core.md",
        personal_skill_set_directory=tmp_path / "personal-skill-set",
        extend_workspace_with_global_skills=False,
        requested_skill_source_directories=[],
        workspace_search_root_directory=tmp_path / "workspace",
        claude_binary_path="/bin/claude",
    )

    assert launch_plan.loaded_skill_names == ["core", "personal-skills"]
    assert launch_plan.command_arguments == ["/bin/claude"]


def test_prepare_workspace_claude_launch_plan_rejects_missing_default_injected_skill(
    tmp_path,
):
    global_claude_config_directory = tmp_path / "global-claude"
    (global_claude_config_directory / "skills" / "core").mkdir(parents=True)
    (global_claude_config_directory / "skills" / "core" / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )

    with pytest.raises(
        loaded_workspace_launcher_module.WorkspaceLaunchConfigurationError
    ):
        loaded_workspace_launcher_module.prepare_workspace_claude_launch_plan(
            temporary_workspace_directory=tmp_path / "temporary-workspace",
            global_claude_config_directory=global_claude_config_directory,
            global_claude_state_file=tmp_path / "missing-claude-state.json",
            core_instructions_file=tmp_path / "core.md",
            personal_skill_set_directory=tmp_path / "personal-skill-set",
            extend_workspace_with_global_skills=False,
            requested_skill_source_directories=[],
            workspace_search_root_directory=tmp_path / "workspace",
            claude_binary_path="/bin/claude",
        )


def test_prepare_workspace_claude_launch_plan_skips_duplicate_local_skill_directory_names(
    tmp_path,
):
    global_claude_config_directory = tmp_path / "global-claude"
    (global_claude_config_directory / "skills" / "core").mkdir(parents=True)
    (global_claude_config_directory / "skills" / "core" / "SKILL.md").write_text(
        "---\nname: core\n---\n"
    )
    (global_claude_config_directory / "skills" / "personal-skills").mkdir(parents=True)
    (
        global_claude_config_directory / "skills" / "personal-skills" / "SKILL.md"
    ).write_text("---\nname: personal-skills\n---\n")

    workspace_directory = tmp_path / "workspace"
    preferred_browser_skill_directory = (
        workspace_directory / "agents" / "skills" / "browser"
    )
    preferred_browser_skill_directory.mkdir(parents=True)
    (preferred_browser_skill_directory / "SKILL.md").write_text(
        "---\nname: browser\n---\n"
    )

    duplicate_browser_skill_directory_in_claude_worktree = (
        workspace_directory
        / ".claude"
        / "worktrees"
        / "nested-worktree"
        / "agents"
        / "skills"
        / "browser"
    )
    duplicate_browser_skill_directory_in_claude_worktree.mkdir(parents=True)
    (duplicate_browser_skill_directory_in_claude_worktree / "SKILL.md").write_text(
        "---\nname: browser-duplicate\n---\n"
    )

    duplicate_browser_skill_directory_in_workspace_worktree = (
        workspace_directory
        / ".worktrees"
        / "another-worktree"
        / "agents"
        / "skills"
        / "browser"
    )
    duplicate_browser_skill_directory_in_workspace_worktree.mkdir(parents=True)
    (duplicate_browser_skill_directory_in_workspace_worktree / "SKILL.md").write_text(
        "---\nname: browser-duplicate\n---\n"
    )

    launch_plan = loaded_workspace_launcher_module.prepare_workspace_claude_launch_plan(
        temporary_workspace_directory=tmp_path / "temporary-workspace",
        global_claude_config_directory=global_claude_config_directory,
        global_claude_state_file=tmp_path / "missing-claude-state.json",
        core_instructions_file=tmp_path / "core.md",
        personal_skill_set_directory=tmp_path / "personal-skill-set",
        extend_workspace_with_global_skills=False,
        requested_skill_source_directories=[],
        workspace_search_root_directory=workspace_directory,
        claude_binary_path="/bin/claude",
    )

    assert (
        launch_plan.config_directory / "skills" / "browser"
    ).resolve() == preferred_browser_skill_directory.resolve()
    assert launch_plan.loaded_skill_names == ["browser", "core", "personal-skills"]


def test_resolve_requested_skill_source_directories_requires_skill_markdown(tmp_path):
    missing_skill_markdown_directory = tmp_path / "without-skill-markdown"
    missing_skill_markdown_directory.mkdir()

    with pytest.raises(
        loaded_workspace_launcher_module.WorkspaceLaunchConfigurationError
    ):
        loaded_workspace_launcher_module.resolve_requested_skill_source_directories(
            [str(missing_skill_markdown_directory)]
        )


def test_compute_deterministic_workspace_directory_is_stable_for_same_path(tmp_path):
    project_directory = tmp_path / "my-project"
    project_directory.mkdir()

    first_result = (
        loaded_workspace_launcher_module.compute_deterministic_workspace_directory(
            project_directory
        )
    )
    second_result = (
        loaded_workspace_launcher_module.compute_deterministic_workspace_directory(
            project_directory
        )
    )

    assert first_result == second_result
    assert "/tmp/claude-workspace." in str(first_result)


def test_compute_deterministic_workspace_directory_differs_for_different_paths(
    tmp_path,
):
    first_directory = tmp_path / "project-a"
    second_directory = tmp_path / "project-b"
    first_directory.mkdir()
    second_directory.mkdir()

    first_result = (
        loaded_workspace_launcher_module.compute_deterministic_workspace_directory(
            first_directory
        )
    )
    second_result = (
        loaded_workspace_launcher_module.compute_deterministic_workspace_directory(
            second_directory
        )
    )

    assert first_result != second_result


def test_atomically_replace_global_credentials_file_with_workspace_copy_propagates_changes(
    tmp_path,
):
    workspace_credentials_file = tmp_path / "workspace-credentials.json"
    global_claude_credentials_file = tmp_path / "global-credentials.json"
    workspace_credentials_file.write_text('{"refreshed":true}\n')
    global_claude_credentials_file.write_text('{"refreshed":false}\n')

    loaded_workspace_launcher_module.atomically_replace_global_credentials_file_with_workspace_copy(
        workspace_credentials_file, global_claude_credentials_file
    )

    assert global_claude_credentials_file.read_text() == '{"refreshed":true}\n'
    assert global_claude_credentials_file.stat().st_mode & 0o777 == 0o600


def test_seed_workspace_credentials_file_from_global_copies_when_global_exists(
    tmp_path,
):
    workspace_config_directory = tmp_path / "workspace-config"
    workspace_config_directory.mkdir()
    global_claude_credentials_file = tmp_path / "global-credentials.json"
    global_claude_credentials_file.write_text('{"token":"abc"}\n')

    loaded_workspace_launcher_module.seed_workspace_credentials_file_from_global(
        workspace_config_directory, global_claude_credentials_file
    )

    workspace_credentials_file = workspace_config_directory / ".credentials.json"
    assert workspace_credentials_file.is_file()
    assert not workspace_credentials_file.is_symlink()
    assert workspace_credentials_file.read_text() == '{"token":"abc"}\n'
    assert workspace_credentials_file.stat().st_mode & 0o777 == 0o600


def test_seed_workspace_credentials_file_from_global_skips_when_global_missing(
    tmp_path,
):
    workspace_config_directory = tmp_path / "workspace-config"
    workspace_config_directory.mkdir()
    global_claude_credentials_file = tmp_path / "missing-global-credentials.json"

    loaded_workspace_launcher_module.seed_workspace_credentials_file_from_global(
        workspace_config_directory, global_claude_credentials_file
    )

    assert not (workspace_config_directory / ".credentials.json").exists()


def test_recreate_workspace_directory_removes_existing_content(tmp_path):
    workspace_directory = tmp_path / "workspace"
    workspace_directory.mkdir()
    (workspace_directory / "stale-file.txt").write_text("old")

    loaded_workspace_launcher_module.recreate_workspace_directory(workspace_directory)

    assert not workspace_directory.exists()
