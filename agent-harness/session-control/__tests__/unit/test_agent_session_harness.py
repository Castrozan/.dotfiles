import pytest

from agent_session import harness


@pytest.mark.parametrize(
    ("command_line", "expected_harness"),
    [
        ("/nix/store/example/bin/claude --session-id 123", "claude"),
        ("/nix/store/example/bin/codex --no-alt-screen", "codex"),
        ("/nix/store/example/bin/opencode --continue", "opencode"),
    ],
)
def test_identifies_each_supported_harness(command_line, expected_harness):
    assert harness.harness_name_for_command(command_line) == expected_harness


def test_walks_past_shells_to_find_the_agent_harness(monkeypatch):
    process_records = {
        100: (101, "/bin/bash -lc tool"),
        101: (102, "/bin/zsh"),
        102: (1, "/nix/store/example/bin/opencode"),
    }
    monkeypatch.setattr(
        harness,
        "process_info_for",
        lambda process_identifier: process_records.get(process_identifier),
    )

    assert harness.find_agent_session(100) == (
        102,
        "opencode",
        "/nix/store/example/bin/opencode",
    )


@pytest.mark.parametrize(
    ("harness_name", "session_identifier", "expected_command"),
    [
        ("claude", "session-123", ["claude", "--resume", "session-123"]),
        ("codex", "session-123", ["codex", "resume", "session-123"]),
        ("opencode", "session-123", ["opencode", "--session", "session-123"]),
    ],
)
def test_builds_each_harness_native_resume_command(
    harness_name, session_identifier, expected_command
):
    assert (
        harness.resume_command_for(harness_name, session_identifier) == expected_command
    )


@pytest.mark.parametrize(
    ("harness_name", "command_line", "expected_session_identifier"),
    [
        ("claude", "claude --resume session-123", "session-123"),
        ("claude", "claude -r session-123", "session-123"),
        ("claude", "claude --session-id session-123", "session-123"),
        ("claude", "claude -r --no-chrome", None),
        ("codex", "codex resume session-123", "session-123"),
        ("codex", "codex resume --all session-123", "session-123"),
        ("codex", "codex resume --config model=fast session-123", "session-123"),
        ("codex", "codex resume --local-provider ollama session-123", "session-123"),
        ("codex", "codex resume --image first.png second.png session-123", None),
        ("codex", "codex resume --image=first.png second.png session-123", None),
        ("codex", "codex resume -ifirst.png second.png session-123", None),
        ("codex", "codex resume --last continue-the-task", None),
        ("codex", "codex continue and resume session-123", None),
        ("opencode", "opencode --session session-123", "session-123"),
        ("opencode", "opencode --continue", None),
    ],
)
def test_extracts_a_live_session_identifier_when_the_harness_exposes_one(
    harness_name, command_line, expected_session_identifier
):
    assert (
        harness.session_identifier_from_command(harness_name, command_line)
        == expected_session_identifier
    )
