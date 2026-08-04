from pathlib import Path
from unittest.mock import patch

from agent_commit_provenance.session_identity import (
    AgentSessionIdentity,
    resolve_agent_session_identity,
)

CLAUDE_SESSION_ENVIRONMENT = {
    "CLAUDE_CODE_SESSION_ID": "c0f2de6b-80e4-4f90-9c6c-7a43a55aa5d9",
    "AGENT_COMMIT_PROVENANCE_MACHINE": "rin",
}


class TestResolveFromEnvironment:
    def test_claude_session_identifier_wins_without_touching_process_ancestry(self):
        with patch(
            "agent_commit_provenance.session_identity.find_agent_session"
        ) as ancestry_lookup:
            identity = resolve_agent_session_identity(
                CLAUDE_SESSION_ENVIRONMENT, 4242, Path("/repo")
            )
        ancestry_lookup.assert_not_called()
        assert identity == AgentSessionIdentity(
            harness_name="claude",
            machine_name="rin",
            session_identifier="c0f2de6b-80e4-4f90-9c6c-7a43a55aa5d9",
            agent_name=None,
        )

    def test_clawde_agent_name_is_recorded(self):
        environment = CLAUDE_SESSION_ENVIRONMENT | {
            "CLAWDE_AGENT_NAME": "dotfiles-steward"
        }
        identity = resolve_agent_session_identity(environment, 4242, Path("/repo"))
        assert identity.agent_name == "dotfiles-steward"

    def test_machine_name_falls_back_to_the_hostname(self):
        with patch(
            "agent_commit_provenance.session_identity.socket.gethostname",
            return_value="kira.local",
        ):
            identity = resolve_agent_session_identity(
                {"CLAUDE_CODE_SESSION_ID": "abc"}, 4242, Path("/repo")
            )
        assert identity.machine_name == "kira"


class TestResolveFromProcessAncestry:
    def test_resumed_codex_session_identifier_comes_from_the_command_line(self):
        with patch(
            "agent_commit_provenance.session_identity.find_agent_session",
            return_value=(99, "codex", "codex resume 019d91b3-b7cf-7681"),
        ):
            identity = resolve_agent_session_identity({}, 4242, Path("/repo"))
        assert identity.harness_name == "codex"
        assert identity.session_identifier == "019d91b3-b7cf-7681"

    def test_fresh_codex_session_is_resolved_from_the_rollout_store(self):
        with (
            patch(
                "agent_commit_provenance.session_identity.find_agent_session",
                return_value=(99, "codex", "codex"),
            ),
            patch(
                "agent_commit_provenance.session_identity.codex_session_identifier_for_working_directory",
                return_value="019fafd2-8d5c-70a2",
            ),
        ):
            identity = resolve_agent_session_identity({}, 4242, Path("/repo"))
        assert identity.session_identifier == "019fafd2-8d5c-70a2"

    def test_fresh_opencode_session_records_the_harness_without_a_session(self):
        with patch(
            "agent_commit_provenance.session_identity.find_agent_session",
            return_value=(99, "opencode", "opencode"),
        ):
            identity = resolve_agent_session_identity({}, 4242, Path("/repo"))
        assert identity.harness_name == "opencode"
        assert identity.session_identifier is None

    def test_commit_outside_any_agent_session_has_no_identity(self):
        with patch(
            "agent_commit_provenance.session_identity.find_agent_session",
            return_value=None,
        ):
            assert resolve_agent_session_identity({}, 4242, Path("/repo")) is None


class TestResumeCommand:
    def test_claude_resume_command_carries_the_session(self):
        identity = AgentSessionIdentity("claude", "rin", "abc-123", None)
        assert identity.resume_command() == "claude --resume abc-123"

    def test_codex_resume_command_carries_the_session(self):
        identity = AgentSessionIdentity("codex", "rin", "abc-123", None)
        assert identity.resume_command() == "codex resume abc-123"

    def test_opencode_resume_command_carries_the_session(self):
        identity = AgentSessionIdentity("opencode", "rin", "abc-123", None)
        assert identity.resume_command() == "opencode --session abc-123"

    def test_no_resume_command_without_a_session_identifier(self):
        identity = AgentSessionIdentity("opencode", "rin", None, None)
        assert identity.resume_command() is None
