import json

from compaction_replay import replay_session
from session_parsing import parse_session
from turn_cost import Turn


def assistant_record(message_id, output_tokens):
    return {
        "type": "assistant",
        "message": {
            "id": message_id,
            "model": "model-under-test",
            "usage": {
                "input_tokens": 1,
                "cache_read_input_tokens": 10,
                "cache_creation_input_tokens": 5,
                "cache_creation": {"ephemeral_1h_input_tokens": 5},
                "output_tokens": output_tokens,
            },
            "content": [
                {
                    "type": "tool_use",
                    "id": "call-1",
                    "name": "Read",
                    "input": {"file_path": "/a"},
                }
            ],
        },
    }


def tool_result_record():
    return {
        "type": "user",
        "message": {
            "content": [
                {"type": "tool_result", "tool_use_id": "call-1", "content": "abcd"}
            ]
        },
    }


def write_session(tmp_path, records):
    path = tmp_path / "project" / "session.jsonl"
    path.parent.mkdir()
    path.write_text("\n".join(json.dumps(record) for record in records))
    return path


def test_repeated_assistant_message_counts_one_turn_with_final_usage(tmp_path):
    path = write_session(
        tmp_path, [assistant_record("m1", 2), assistant_record("m1", 7)]
    )

    session = parse_session(path)

    assert [turn.output for turn in session.turns] == [7]


def test_repeated_tool_result_counts_one_call(tmp_path):
    path = write_session(
        tmp_path,
        [assistant_record("m1", 2), tool_result_record(), tool_result_record()],
    )

    session = parse_session(path)

    assert session.tool_calls["Read"] == 1
    assert session.tool_text_bytes["Read"] == 4


def turn_with_context(context):
    return Turn(0, context, 0, 0, 0)


def test_replay_compacts_once_when_context_crosses_the_threshold():
    turns = [
        turn_with_context(context) for context in (10_000, 60_000, 110_000, 160_000)
    ]

    _, compactions = replay_session(turns, threshold=100_000)

    assert compactions == 1


def test_replay_never_compacts_below_the_threshold():
    turns = [
        turn_with_context(context) for context in (10_000, 60_000, 110_000, 160_000)
    ]

    _, compactions = replay_session(turns, threshold=1_000_000)

    assert compactions == 0
