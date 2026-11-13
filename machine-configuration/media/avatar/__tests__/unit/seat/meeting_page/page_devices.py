from pathlib import Path

MEETING_SEAT = (
    Path(__file__).resolve().parents[4]
    / "scripts/conversation/remote_seat/page/meeting-seat.js"
)


def device(kind, device_id, label):
    return {"kind": kind, "deviceId": device_id, "label": label}


CALL_MICROPHONE = device("audiooutput", "out-2", "BlackHole 2ch (Virtual)")
CALL_SPEAKER = device("audioinput", "in-16", "BlackHole 16ch (Virtual)")
BUILT_IN_OUTPUT = device("audiooutput", "out-1", "MacBook Pro Speakers (Built-in)")
BUILT_IN_INPUT = device("audioinput", "in-1", "MacBook Pro Microphone (Built-in)")
BLACKHOLE_OUTPUT_AS_DEFAULT = device(
    "audiooutput", "default", "Default - BlackHole 2ch (Virtual)"
)
BLACKHOLE_INPUT_FOR_THE_WRONG_DIRECTION = device(
    "audioinput", "in-2", "BlackHole 2ch (Virtual)"
)
