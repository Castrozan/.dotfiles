import json

from agent_commit_provenance.transcript_locations import (
    transcript_path_for_session,
    user_prompts_in_transcript,
)


def write_transcript_records(transcript_path, records):
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
    )


class TestTranscriptPathForSession:
    def test_finds_a_claude_transcript_under_any_project_directory(self, tmp_path):
        claude_projects_directory = tmp_path / "projects"
        transcript_path = (
            claude_projects_directory / "-Users-someone--dotfiles" / "abc-123.jsonl"
        )
        write_transcript_records(transcript_path, [])
        assert (
            transcript_path_for_session(
                "claude", "abc-123", claude_projects_directory, tmp_path / "codex"
            )
            == transcript_path
        )

    def test_finds_a_codex_rollout_by_its_session_suffix(self, tmp_path):
        codex_sessions_directory = tmp_path / "codex"
        rollout_path = (
            codex_sessions_directory
            / "2026"
            / "08"
            / "04"
            / "rollout-2026-08-04T10-00-00-abc-123.jsonl"
        )
        write_transcript_records(rollout_path, [])
        assert (
            transcript_path_for_session(
                "codex", "abc-123", tmp_path / "projects", codex_sessions_directory
            )
            == rollout_path
        )

    def test_a_pruned_transcript_resolves_to_nothing(self, tmp_path):
        assert (
            transcript_path_for_session(
                "claude", "gone", tmp_path / "projects", tmp_path / "codex"
            )
            is None
        )


class TestUserPromptsInTranscript:
    def test_claude_prompts_skip_subagents_tool_results_and_meta_records(
        self, tmp_path
    ):
        transcript_path = tmp_path / "abc-123.jsonl"
        write_transcript_records(
            transcript_path,
            [
                {"type": "user", "message": {"content": "add the tracking hook"}},
                {"type": "assistant", "message": {"content": "working on it"}},
                {
                    "type": "user",
                    "isSidechain": True,
                    "message": {"content": "subagent brief"},
                },
                {"type": "user", "isMeta": True, "message": {"content": "meta noise"}},
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {"type": "tool_result", "content": "command output"}
                        ]
                    },
                },
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "now ship it"}]},
                },
            ],
        )
        assert user_prompts_in_transcript("claude", transcript_path) == [
            "add the tracking hook",
            "now ship it",
        ]

    def test_codex_prompts_come_from_user_message_events(self, tmp_path):
        rollout_path = tmp_path / "rollout-abc-123.jsonl"
        write_transcript_records(
            rollout_path,
            [
                {"type": "session_meta", "payload": {"id": "abc-123"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "refactor this"},
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "agent_message", "message": "done"},
                },
            ],
        )
        assert user_prompts_in_transcript("codex", rollout_path) == ["refactor this"]

    def test_a_corrupt_transcript_line_does_not_stop_the_read(self, tmp_path):
        transcript_path = tmp_path / "abc-123.jsonl"
        transcript_path.write_text(
            "not json\n"
            + json.dumps({"type": "user", "message": {"content": "still readable"}})
            + "\n",
            encoding="utf-8",
        )
        assert user_prompts_in_transcript("claude", transcript_path) == [
            "still readable"
        ]
