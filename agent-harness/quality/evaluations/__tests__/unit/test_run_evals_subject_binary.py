import pytest

from instruction_surface_scanner import REPO_ROOT
from run_evals_subject_binary import (
    SUBJECT_BINARY_OVERRIDE,
    appends_the_interactive_surface,
    resolve_subject_claude_binary,
)

EVALUATION_ROOT = REPO_ROOT / "agent-harness" / "quality" / "evaluations"
SURFACE_FREE_CALLERS = (
    EVALUATION_ROOT / "run_evals_claude_cli.py",
    EVALUATION_ROOT / "integration" / "ab_test_claude_session.py",
    EVALUATION_ROOT / "e2e" / "coached_compliance_reviewer.py",
)
DEPLOYED_SESSION_SUBJECT = EVALUATION_ROOT / "integration" / "integration_session.py"
EVALUATION_PACKAGING_PATH = EVALUATION_ROOT / "agent-evaluations-home-manager.nix"


def write_launcher(directory, body: str):
    launcher = directory / "claude"
    launcher.write_text(body, encoding="utf-8")
    launcher.chmod(0o755)
    return launcher


def test_the_interactive_wrapper_is_recognised_by_its_append_flag(tmp_path):
    wrapper = write_launcher(
        tmp_path, '#!/bin/bash\nexec claude --append-system-prompt-file "$f" "$@"\n'
    )
    plain_directory = tmp_path / "plain"
    plain_directory.mkdir()
    unwrapped = write_launcher(plain_directory, '#!/bin/bash\nexec claude "$@"\n')

    assert appends_the_interactive_surface(str(wrapper))
    assert not appends_the_interactive_surface(str(unwrapped))


def test_a_compiled_binary_is_never_read_as_the_wrapper(tmp_path):
    bundle = tmp_path / "claude"
    bundle.write_bytes(b"\x7fELF" + b"--append-system-prompt-file" * 8)

    assert not appends_the_interactive_surface(str(bundle))


def test_resolution_skips_a_wrapped_launcher_for_an_unwrapped_one(
    tmp_path, monkeypatch
):
    wrapped_directory = tmp_path / "wrapped"
    unwrapped_directory = tmp_path / "unwrapped"
    wrapped_directory.mkdir()
    unwrapped_directory.mkdir()
    write_launcher(
        wrapped_directory,
        '#!/bin/bash\nexec claude --append-system-prompt-file "$f" "$@"\n',
    )
    unwrapped = write_launcher(unwrapped_directory, '#!/bin/bash\nexec claude "$@"\n')
    monkeypatch.delenv(SUBJECT_BINARY_OVERRIDE, raising=False)
    monkeypatch.setenv("PATH", f"{wrapped_directory}:{unwrapped_directory}")

    assert resolve_subject_claude_binary() == str(unwrapped)


def test_resolution_refuses_rather_than_measuring_the_live_machine(
    tmp_path, monkeypatch
):
    wrapped_directory = tmp_path / "wrapped"
    wrapped_directory.mkdir()
    write_launcher(
        wrapped_directory,
        '#!/bin/bash\nexec claude --append-system-prompt-file "$f" "$@"\n',
    )
    monkeypatch.delenv(SUBJECT_BINARY_OVERRIDE, raising=False)
    monkeypatch.setenv("PATH", str(wrapped_directory))

    with pytest.raises(RuntimeError, match="interactive wrapper"):
        resolve_subject_claude_binary()


def test_no_scored_caller_inherits_the_reply_shape_surface():
    for caller_path in SURFACE_FREE_CALLERS:
        source = caller_path.read_text(encoding="utf-8")

        assert "resolve_subject_claude_binary()" in source, (
            f"{caller_path.name} scores against instructions it supplies itself, so a bare "
            "'claude' from PATH would resolve the interactive wrapper and fold the always-on "
            "surface into every arm and every verdict"
        )


def test_the_end_to_end_judge_is_pinned_without_unwrapping_the_subject():
    packaging = EVALUATION_PACKAGING_PATH.read_text(encoding="utf-8")
    agent_e2e_definition = packaging.split('writeShellScriptBin "agent-e2e"', 1)[
        1
    ].split("'';", 1)[0]

    assert "AGENT_EVAL_CLAUDE_BINARY" in agent_e2e_definition, (
        "the compliance judge subtracts fifteen NPS points per finding, so it must grade "
        "from the instructions it was handed rather than from the live reply-shape surface"
    )
    assert "makeBinPath" in agent_e2e_definition
    assert "unwrappedPackage" not in agent_e2e_definition.split("makeBinPath", 1)[1], (
        "end-to-end scenarios score the deployed session, so the herdr-driven subject must "
        "keep resolving the interactive wrapper from PATH"
    )


def test_the_deployed_session_suite_keeps_the_interactive_wrapper():
    source = DEPLOYED_SESSION_SUBJECT.read_text(encoding="utf-8")

    assert "resolve_subject_claude_binary" not in source, (
        "integration scenarios score the deployed session, so stripping the interactive "
        "wrapper from this subject would measure a configuration no human ever runs"
    )
