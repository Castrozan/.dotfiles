from agent_commit_provenance.commit_trailers import (
    parse_agent_provenance_trailers,
    trailers_for_identity,
)
from agent_commit_provenance.session_identity import AgentSessionIdentity


class TestTrailersForIdentity:
    def test_an_interactive_claude_session_records_four_trailers(self):
        identity = AgentSessionIdentity("claude", "rin", "abc-123", None)
        assert trailers_for_identity(identity) == [
            "Agent-Harness: claude",
            "Agent-Machine: rin",
            "Agent-Session: abc-123",
            "Agent-Resume: claude --resume abc-123",
        ]

    def test_a_fleet_agent_also_records_its_name(self):
        identity = AgentSessionIdentity("claude", "chise", "abc-123", "chise-steward")
        assert "Agent-Name: chise-steward" in trailers_for_identity(identity)

    def test_a_session_without_an_identifier_records_no_resume_command(self):
        identity = AgentSessionIdentity("opencode", "kira", None, None)
        assert trailers_for_identity(identity) == [
            "Agent-Harness: opencode",
            "Agent-Machine: kira",
        ]


class TestParseAgentProvenanceTrailers:
    def test_reads_back_the_trailers_a_commit_carries(self):
        commit_message = "\n".join(
            [
                "feat(dev): track which agent session made a commit",
                "",
                "Body line that mentions Agent-Session: not-a-trailer inline",
                "",
                "Signed-off-by: Someone <someone@example.com>",
                "Agent-Harness: claude",
                "Agent-Machine: rin",
                "Agent-Session: abc-123",
                "Agent-Resume: claude --resume abc-123",
            ]
        )
        assert parse_agent_provenance_trailers(commit_message) == {
            "Agent-Harness": "claude",
            "Agent-Machine": "rin",
            "Agent-Session": "abc-123",
            "Agent-Resume": "claude --resume abc-123",
        }

    def test_a_hand_written_commit_carries_nothing(self):
        assert parse_agent_provenance_trailers("fix: a commit made by hand\n") == {}
