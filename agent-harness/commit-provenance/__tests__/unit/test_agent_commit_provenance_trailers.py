from agent_commit_provenance.commit_trailers import trailers_for_identity
from agent_commit_provenance.session_identity import AgentSessionIdentity


class TestTrailersForIdentity:
    def test_an_interactive_claude_session_records_where_and_how_to_resume(self):
        identity = AgentSessionIdentity("claude", "rin", "abc-123", None)
        assert trailers_for_identity(identity) == [
            "Agent-Machine: rin",
            "Agent-Resume: claude --resume abc-123",
        ]

    def test_a_fleet_agent_also_records_its_name(self):
        identity = AgentSessionIdentity("claude", "chise", "abc-123", "chise-steward")
        assert "Agent-Name: chise-steward" in trailers_for_identity(identity)

    def test_a_session_without_an_identifier_records_no_resume_command(self):
        identity = AgentSessionIdentity("opencode", "kira", None, None)
        assert trailers_for_identity(identity) == ["Agent-Machine: kira"]
