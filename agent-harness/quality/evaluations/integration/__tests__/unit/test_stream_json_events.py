from stream_json_events import decode_stream_json_events


def test_decodes_each_json_line_in_order():
    raw_output = '{"type": "assistant"}\n{"type": "result", "result": "done"}\n'

    assert list(decode_stream_json_events(raw_output)) == [
        {"type": "assistant"},
        {"type": "result", "result": "done"},
    ]


def test_skips_blank_lines_and_undecodable_lines():
    raw_output = '{"type": "assistant"}\n\n   \nnot json\n{"type": "result"}\n'

    assert list(decode_stream_json_events(raw_output)) == [
        {"type": "assistant"},
        {"type": "result"},
    ]


def test_empty_output_yields_no_events():
    assert list(decode_stream_json_events("")) == []
