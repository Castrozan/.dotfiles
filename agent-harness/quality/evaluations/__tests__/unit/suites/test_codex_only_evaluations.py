from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from hypothesis import given, strategies

import codex_only_evaluations

EVALUATIONS_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def evaluation_project(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    config = tmp_path / "evals/config.yaml"
    config.parent.mkdir()
    config.write_text(
        yaml.safe_dump(
            {
                "projeto": "dotfiles-agent-instructions",
                "sujeito": {"cliente": "codex"},
                "juiz": {"cliente": "codex"},
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_EVALS_CONFIG", raising=False)
    monkeypatch.delenv("AGENT_EVALS_SOURCE_ROOT", raising=False)
    return config


@pytest.mark.parametrize("flag", ("--client", "--cliente"))
@pytest.mark.parametrize("client", ("claude", "opencode", "", "CODEX"))
@pytest.mark.parametrize("joined", (False, True))
def test_non_codex_overrides_are_rejected_before_execution(
    evaluation_project, monkeypatch, flag, client, joined
):
    arguments = ["run", f"{flag}={client}"] if joined else ["run", flag, client]
    launch = Mock()
    monkeypatch.setattr(codex_only_evaluations.os, "execv", launch)
    with pytest.raises(ValueError, match="Codex"):
        codex_only_evaluations.execute_guarded_evaluations(
            "/upstream/agent-evals", arguments
        )
    launch.assert_not_called()


@given(
    strategies.lists(
        strategies.sampled_from(("claude", "opencode", "codex")),
        min_size=1,
        max_size=12,
    )
)
def test_every_repeated_client_selection_must_be_codex(clients):
    arguments = ["run", *(f"--client={client}" for client in clients)]
    if all(client == "codex" for client in clients):
        codex_only_evaluations.require_codex_arguments(arguments)
    else:
        with pytest.raises(ValueError, match="Codex"):
            codex_only_evaluations.require_codex_arguments(arguments)


@pytest.mark.parametrize("section", ("sujeito", "juiz"))
@pytest.mark.parametrize(
    "settings", ({"cliente": "claude"}, {"cliente": "opencode"}, {})
)
def test_subject_and_judge_cannot_inherit_or_select_claude(
    evaluation_project, section, settings
):
    configuration = yaml.safe_load(evaluation_project.read_text())
    configuration[section] = settings
    evaluation_project.write_text(yaml.safe_dump(configuration))
    with pytest.raises(ValueError, match="Codex"):
        codex_only_evaluations.execute_guarded_evaluations(
            "/upstream/agent-evals", ["baseline", "--rodar"]
        )


def test_codex_arguments_and_environment_reach_the_existing_runner(
    evaluation_project, monkeypatch
):
    launch = Mock()
    monkeypatch.setattr(codex_only_evaluations.os, "execv", launch)
    arguments = ["run", "--client=codex", "--case", "one", "--dry-run"]
    codex_only_evaluations.execute_guarded_evaluations(
        "/upstream/agent-evals", arguments
    )
    launch.assert_called_once_with(
        "/upstream/agent-evals", ["/upstream/agent-evals", *arguments]
    )


def test_relative_config_resolves_from_git_root_in_a_subdirectory(
    evaluation_project, monkeypatch
):
    nested = evaluation_project.parent / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    monkeypatch.setenv("AGENT_EVALS_CONFIG", "evals/config.yaml")
    assert codex_only_evaluations.resolved_configuration_path() == evaluation_project


def test_english_configuration_keys_obey_the_same_policy(
    evaluation_project, monkeypatch
):
    evaluation_project.write_text(
        yaml.safe_dump(
            {
                "project": "dotfiles-agent-instructions",
                "subject": {"client": "codex"},
                "judge": {"client": "claude"},
            }
        )
    )
    with pytest.raises(ValueError, match="Codex"):
        codex_only_evaluations.execute_guarded_evaluations(
            "/upstream/agent-evals", ["run"]
        )


def test_unrelated_projects_keep_their_existing_clients(
    evaluation_project, monkeypatch
):
    evaluation_project.write_text(
        yaml.safe_dump({"projeto": "work-project", "sujeito": {"cliente": "claude"}})
    )
    launch = Mock()
    monkeypatch.setattr(codex_only_evaluations.os, "execv", launch)
    codex_only_evaluations.execute_guarded_evaluations(
        "/upstream/agent-evals", ["run", "--client=claude"]
    )
    launch.assert_called_once()


@pytest.mark.parametrize("content", (None, "", "null"))
def test_missing_and_empty_scoped_configs_cannot_inherit_claude(
    evaluation_project, monkeypatch, content
):
    if content is None:
        evaluation_project.unlink()
    else:
        evaluation_project.write_text(content)
    monkeypatch.setattr(
        codex_only_evaluations, "repository_is_personal_tooling", lambda directory: True
    )
    with pytest.raises(ValueError, match="Codex"):
        codex_only_evaluations.execute_guarded_evaluations(
            "/upstream/agent-evals", ["run"]
        )


def test_repository_config_names_only_codex_models_and_clients():
    configuration = yaml.safe_load((EVALUATIONS_ROOT / "config.yaml").read_text())
    assert configuration["sujeito"]["cliente"] == "codex"
    assert configuration["juiz"]["cliente"] == "codex"
    assert set(configuration["modelo_padrao"]) == {"codex"}
    assert set(configuration["esforco_padrao"]) == {"codex"}
