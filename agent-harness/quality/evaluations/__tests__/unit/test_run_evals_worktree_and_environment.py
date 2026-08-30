from instruction_surface_scanner import REPO_ROOT
from run_evals_fingerprint import evaluation_runner_paths
from run_evals_worktree_and_environment import (
    build_filtered_environment,
)

EVALUATION_PACKAGING_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "quality"
    / "evaluations"
    / "agent-evaluations-home-manager.nix"
)


def test_isolation_strips_the_interactive_reply_shape_marker(monkeypatch):
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH", "/some/interactive/preferences.md"
    )
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    filtered = build_filtered_environment()

    assert "AGENT_INTERACTIVE_PREFERENCES_PATH" not in filtered
    assert "CLAUDECODE" not in filtered
    assert filtered["PATH"] == "/usr/bin:/bin"


def test_the_measured_subjects_bypass_the_interactive_wrappers():
    packaging = EVALUATION_PACKAGING_PATH.read_text(encoding="utf-8")
    agent_eval_definition = packaging.split('writeShellScriptBin "agent-eval"', 1)[
        1
    ].split("'';", 1)[0]

    for harness in ("claude", "codex", "opencode"):
        assert f"config.{harness}.unwrappedPackage" in agent_eval_definition
    assert "AGENT_EVAL_CLAUDE_BINARY" in agent_eval_definition
    assert "AGENT_EVAL_CODEX_BINARY" in agent_eval_definition
    assert "config.claude.unwrappedPackage" in agent_eval_definition, (
        "the interactive wrapper appends the always-on reply-shape surface to every launch, "
        "including `-p --system-prompt` with the isolation variables stripped, so an eval that "
        "resolves the wrapped claude scores the live machine instead of the instruction paths "
        "its suite declares and its fingerprint records"
    )


def test_the_subject_launcher_is_fingerprinted():
    assert EVALUATION_PACKAGING_PATH in evaluation_runner_paths(REPO_ROOT), (
        "the packaging chooses which claude binary every sample runs against, and swapping the "
        "wrapped launcher for the unwrapped one moved this suite by seventeen points, so a "
        "baseline recorded under one launcher must not validate against another"
    )


def test_the_vendor_sdk_runtime_is_fingerprinted():
    runtime_paths = evaluation_runner_paths(REPO_ROOT)

    for relative_path in (
        "node-provider-runtime-package.nix",
        "node-provider-runtime/package.json",
        "node-provider-runtime/package-lock.json",
        "node-provider-runtime/provider-runtime.mjs",
    ):
        assert EVALUATION_PACKAGING_PATH.parent / relative_path in runtime_paths
