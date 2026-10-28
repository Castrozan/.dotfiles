import json


def decode_stream_json_events(raw_output: str):
    for line in raw_output.strip().split("\n"):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue
