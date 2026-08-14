import json

import pytest

from end_of_turn_format_guard_test_support import (
    invoke_guard,
    stop_payload,
    write_transcript_from_events,
)


@pytest.mark.parametrize("surface", ("claude", "codex", "opencode", "pi"))
def test_all_surfaces_block_from_explicit_text_without_a_transcript(surface):
    payload = {
        "hook_event_name": "Stop",
        "session_id": "direct-text",
        "user_request_text": "summarize the result",
        "reply_text": "Sure, done. **Done:** x\n**Next:** y",
    }

    result = invoke_guard(payload, surface=surface)

    assert json.loads(result.stdout)["decision"] == "block"


def test_codex_uses_its_last_assistant_message_and_jsonl_user_request(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "summarize it"}],
                },
            }
        ],
    )
    payload = stop_payload(transcript)
    payload["last_assistant_message"] = "Sure, done. **Done:** x\n**Next:** y"

    result = invoke_guard(payload, surface="codex")

    assert json.loads(result.stdout)["decision"] == "block"


def test_codex_accepts_generic_text_blocks_in_response_items(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "text", "text": "write a document"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Sure, here it is."}],
                },
            },
        ],
    )

    result = invoke_guard(stop_payload(transcript), surface="codex")

    assert json.loads(result.stdout)["decision"] == "block"
