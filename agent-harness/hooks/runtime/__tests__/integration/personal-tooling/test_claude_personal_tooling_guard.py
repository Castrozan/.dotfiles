import json
from itertools import product
from unittest.mock import Mock

import pytest
from hypothesis import given, strategies

import dotfiles_repository_scope
from claude_personal_tooling_guard_handler import handle
from hook_dispatch import CLAUDE_SURFACE, CODEX_SURFACE, HookHandler, run_handlers
from hook_event_output import emit_context_injection, emit_pretooluse_decision


@pytest.fixture
def personal_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("AGENT_EVALS_SOURCE_ROOT", raising=False)
    return tmp_path


@pytest.mark.parametrize(
    "repository_name,remote_template",
    list(
        product(
            (
                ".dotfiles",
                "dotfiles-private",
                "private-config",
                "clawde",
                "agent-evals",
                "herdr",
                "herdr-pace",
                "wellput",
                "cache-tax",
                "cc-crayon",
                "airquote",
                "arr-stack",
            ),
            (
                "git@github.com:Castrozan/{}.git",
                "https://github.com/castrozan/{}",
                "ssh://git@github.com/Castrozan/{}.git",
                "ssh://git@github.com:22/Castrozan/{}.git",
                "https://lucas@github.com/CASTROZAN/{}.GIT",
                "git://github.com/Castrozan/{}.git",
            ),
        )
    ),
)
def test_confirmed_tooling_remotes_are_in_scope(repository_name, remote_template):
    assert dotfiles_repository_scope.remote_identifies_personal_tooling(
        remote_template.format(repository_name)
    )


@given(strategies.from_regex(r"[a-z]{1,24}", fullmatch=True))
def test_repository_name_fragments_do_not_expand_the_scope(repository_name):
    assert not dotfiles_repository_scope.remote_identifies_personal_tooling(
        f"git@github.com:Castrozan/prefix-{repository_name}-suffix.git"
    )


@pytest.mark.parametrize(
    "remote",
    (
        "git@github.com:Coates/clawde.git",
        "https://github.com.evil.invalid/Castrozan/.dotfiles.git",
        "https://gitlab.com/Castrozan/.dotfiles.git",
        "https://github.com/Castrozan/lazygit.git",
        "https://github.com/Castrozan/cbonsai.git",
    ),
)
def test_unrelated_or_uncertain_repositories_are_not_classified(remote):
    assert not dotfiles_repository_scope.remote_identifies_personal_tooling(remote)


@pytest.mark.parametrize("root_name", (".dotfiles", "zanoni-system"))
def test_canonical_checkouts_and_symlinks_are_blocked(personal_home, root_name):
    root = personal_home / root_name
    root.mkdir()
    alias = personal_home / "alias"
    alias.symlink_to(root, target_is_directory=True)
    for directory in (root, root / "nested", alias / "nested"):
        assert dotfiles_repository_scope.repository_is_personal_tooling(str(directory))
    assert not dotfiles_repository_scope.repository_is_personal_tooling(
        str(personal_home / f"{root_name}-unrelated")
    )


def test_relocated_dotfiles_checkout_is_identified_by_its_structure(personal_home):
    root = personal_home / "relocated"
    (root / "agent-harness/quality/evaluations").mkdir(parents=True)
    (root / "repository/flake-assembly").mkdir(parents=True)
    (root / "agent-harness/quality/evaluations/config.yaml").write_text(
        "projeto: dotfiles-agent-instructions"
    )
    (root / "repository/flake-assembly/outputs.nix").touch()
    assert dotfiles_repository_scope.repository_is_personal_tooling(
        str(root / "nested")
    )


def test_git_resolves_related_worktrees_and_non_origin_remotes(
    personal_home, monkeypatch
):
    import subprocess

    root = personal_home / "eval-worktree-fixture"
    root.mkdir()
    (root / ".git").write_text("gitdir: /elsewhere/worktrees/fixture")
    git = Mock(
        return_value=Mock(
            returncode=0,
            stdout="remote.upstream.url git@github.com:Castrozan/.dotfiles.git\n",
        )
    )
    monkeypatch.setattr(subprocess, "run", git)
    assert dotfiles_repository_scope.repository_is_personal_tooling(str(root))
    assert git.call_args.kwargs["timeout"] <= 1


def test_a_worktree_linked_to_dotfiles_is_blocked_without_any_remote(
    personal_home, monkeypatch
):
    import subprocess

    worktree = personal_home / "eval-worktree-local"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: ../.dotfiles/.git/worktrees/local\n")
    git = Mock(
        side_effect=AssertionError("canonical worktree detection needs no subprocess")
    )
    monkeypatch.setattr(subprocess, "run", git)
    assert dotfiles_repository_scope.repository_is_personal_tooling(str(worktree))
    git.assert_not_called()


@pytest.mark.parametrize(
    "event_name", ("SessionStart", "UserPromptSubmit", "PreToolUse")
)
def test_claude_is_stopped_with_codex_guidance(personal_home, capsys, event_name):
    payload = {"hook_event_name": event_name, "cwd": str(personal_home / ".dotfiles")}
    outcome = run_handlers(
        payload, [HookHandler(handle=handle, surfaces=(CLAUDE_SURFACE,))]
    )
    if event_name == "PreToolUse":
        emit_pretooluse_decision(outcome)
        output = json.loads(capsys.readouterr().out)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Use Codex" in output["hookSpecificOutput"]["permissionDecisionReason"]
    else:
        emit_context_injection(event_name, outcome)
        output = json.loads(capsys.readouterr().out)
        assert output["continue"] is False
        assert "Use Codex" in output["stopReason"]


def test_isolated_eval_fixture_keeps_its_source_repository_scope(
    personal_home, monkeypatch
):
    monkeypatch.setenv("AGENT_EVALS_SOURCE_ROOT", str(personal_home / ".dotfiles"))
    assert handle({"cwd": str(personal_home / "e2e-fixture")}) is not None


def test_codex_and_unrelated_claude_sessions_are_unchanged(personal_home):
    assert handle({"cwd": str(personal_home / "work-project")}) is None
    assert handle({}) is None
    outcome = run_handlers(
        {"cwd": str(personal_home / ".dotfiles")},
        [HookHandler(handle=handle, surfaces=(CLAUDE_SURFACE,))],
        CODEX_SURFACE,
    )
    assert outcome.decision is None
