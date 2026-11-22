import json
import threading
import time

import listener

FINISHED = '{"type":"speakAck","status":"finished","source":"elevenlabs"}\n'
INTERRUPTED = '{"type":"speakAck","status":"interrupted","source":"elevenlabs"}\n'


def said(directory, sequence, text, turn_finished=True):
    entry = {
        "sequence": sequence,
        "time": time.time(),
        "source": "human",
        "text": text,
        "speaker": None,
        "turn_finished": turn_finished,
    }
    with (directory / "transcript.jsonl").open("a") as transcript:
        transcript.write(json.dumps(entry) + "\n")


def owner_speaking(directory):
    (directory / listener.SPEECH_IN_PROGRESS_MARKER).touch()


def room_falls_quiet(directory):
    (directory / listener.SPEECH_IN_PROGRESS_MARKER).unlink(missing_ok=True)


def owner_finishes(directory, seconds, words=None):
    def finish():
        if words:
            said(directory, *words)
        room_falls_quiet(directory)

    timer = threading.Timer(seconds, finish)
    timer.start()
    return timer


def outcome(output):
    return json.loads(output.splitlines()[-1])


def withheld_because(reason):
    return {"type": "speakAck", "status": "withheld", "reason": reason}
