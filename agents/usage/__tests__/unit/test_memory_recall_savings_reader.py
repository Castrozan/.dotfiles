import json

import memory_recall_savings_reader


def _write_state_file(state_directory, session_id, state):
    (state_directory / f"memory-recall-{session_id}.json").write_text(json.dumps(state))


class TestReadMemoryRecallSessionStates:
    def test_missing_directory_returns_empty(self, tmp_path):
        assert (
            memory_recall_savings_reader.read_memory_recall_session_states(
                tmp_path / "absent"
            )
            == []
        )

    def test_reads_only_memory_recall_state_files(self, tmp_path):
        _write_state_file(tmp_path, "alpha", {"recall_event_count": 1})
        (tmp_path / "unrelated.json").write_text(json.dumps({"recall_event_count": 99}))
        states = memory_recall_savings_reader.read_memory_recall_session_states(
            tmp_path
        )
        assert states == [{"recall_event_count": 1}]

    def test_corrupt_state_file_is_skipped(self, tmp_path):
        _write_state_file(tmp_path, "good", {"recall_event_count": 2})
        (tmp_path / "memory-recall-bad.json").write_text("{not json")
        states = memory_recall_savings_reader.read_memory_recall_session_states(
            tmp_path
        )
        assert states == [{"recall_event_count": 2}]


class TestSummarizeMemoryRecallSavings:
    def test_empty_states_summarize_to_zeros(self):
        summary = memory_recall_savings_reader.summarize_memory_recall_savings([])
        assert summary["memory_recall_session_count"] == 0
        assert summary["injected_recall_event_count"] == 0
        assert summary["suppressed_recall_event_total"] == 0
        assert summary["suppressed_recall_event_count_by_reason"] == {}
        assert summary["dedup_suppressed_character_total"] == 0

    def test_aggregates_injections_and_suppressions_across_sessions(self):
        states = [
            {
                "recall_event_count": 3,
                "recall_character_total": 900,
                "dedup_suppressed_character_total": 120,
                "suppressed_event_count_by_reason": {"dedup": 2, "budget": 1},
            },
            {
                "recall_event_count": 1,
                "recall_character_total": 100,
                "dedup_suppressed_character_total": 80,
                "suppressed_event_count_by_reason": {"dedup": 1, "debounce": 4},
            },
        ]
        summary = memory_recall_savings_reader.summarize_memory_recall_savings(states)
        assert summary["memory_recall_session_count"] == 2
        assert summary["injected_recall_event_count"] == 4
        assert summary["injected_recall_character_total"] == 1000
        assert summary["dedup_suppressed_character_total"] == 200
        assert summary["suppressed_recall_event_count_by_reason"] == {
            "dedup": 3,
            "budget": 1,
            "debounce": 4,
        }
        assert summary["suppressed_recall_event_total"] == 8

    def test_missing_fields_default_to_zero(self):
        summary = memory_recall_savings_reader.summarize_memory_recall_savings(
            [{"recall_event_count": 5}]
        )
        assert summary["injected_recall_event_count"] == 5
        assert summary["injected_recall_character_total"] == 0
        assert summary["dedup_suppressed_character_total"] == 0
        assert summary["suppressed_recall_event_total"] == 0


class TestSummarizeMemoryRecallSavingsInDirectory:
    def test_directory_summary_matches_manual_aggregate(self, tmp_path):
        _write_state_file(
            tmp_path,
            "one",
            {
                "recall_event_count": 2,
                "suppressed_event_count_by_reason": {"dedup": 1},
                "dedup_suppressed_character_total": 50,
            },
        )
        _write_state_file(
            tmp_path,
            "two",
            {
                "recall_event_count": 1,
                "suppressed_event_count_by_reason": {"budget": 3},
            },
        )
        summary = (
            memory_recall_savings_reader.summarize_memory_recall_savings_in_directory(
                tmp_path
            )
        )
        assert summary["memory_recall_session_count"] == 2
        assert summary["injected_recall_event_count"] == 3
        assert summary["suppressed_recall_event_count_by_reason"] == {
            "dedup": 1,
            "budget": 3,
        }
        assert summary["dedup_suppressed_character_total"] == 50
