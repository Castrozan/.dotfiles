from instruction_surface_scanner import REPO_ROOT
from run_evals_fingerprint import evaluation_runner_paths
from run_evals_worktree_and_environment import build_filtered_environment

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


def test_the_measured_subject_bypasses_the_interactive_wrapper():
    packaging = EVALUATION_PACKAGING_PATH.read_text(encoding="utf-8")
    agent_eval_definition = packaging.split('writeShellScriptBin "agent-eval"', 1)[
        1
    ].split("'';", 1)[0]

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
