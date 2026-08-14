import json

import human_communication_skill_gate_reset_handler
import skill_loaded_marker
from end_of_turn_format_guard_test_support import (
    WELL_FORMED_REPLY,
    invoke_guard,
    stop_payload,
    write_transcript_with_final_assistant_reply,
)


def test_blocks_until_the_humanize_skill_load_is_recorded(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, WELL_FORMED_REPLY
    )

    result = invoke_guard(stop_payload(transcript), humanize_skill_loaded=False)

    parsed = json.loads(result.stdout)
    assert parsed["decision"] == "block"
    assert "Skill(skill='humanize')" in parsed["reason"]


def test_skill_gate_remains_active_during_a_stop_hook_recovery(tmp_path):
    transcript = write_transcript_with_final_assistant_reply(
        tmp_path, WELL_FORMED_REPLY
    )

    result = invoke_guard(
        stop_payload(transcript, stop_hook_active=True),
        humanize_skill_loaded=False,
    )

    assert json.loads(result.stdout)["decision"] == "block"


def test_compaction_clears_humanize_marker_and_requests_a_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))
    skill_loaded_marker.record_skill_loaded("humanize", "session-a")

    outcome = human_communication_skill_gate_reset_handler.handle(
        {"source": "compact", "session_id": "session-a"}
    )

    assert not skill_loaded_marker.has_skill_loaded("humanize", "session-a")
    assert "Skill(skill='humanize')" in outcome.additional_context


def test_non_compaction_session_start_keeps_the_humanize_marker(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))
    skill_loaded_marker.record_skill_loaded("humanize", "session-a")

    outcome = human_communication_skill_gate_reset_handler.handle(
        {"source": "resume", "session_id": "session-a"}
    )

    assert outcome is None
    assert skill_loaded_marker.has_skill_loaded("humanize", "session-a")
