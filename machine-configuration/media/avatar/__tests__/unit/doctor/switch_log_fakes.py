from datetime import datetime

import transcript_log
import voice_turns

HEARD_AT = 1_795_382_485.0
TARGET = "wW:pSP"
OTHER_PANE = "w0:p7"
CONVERSATION = "conversation"
FULL_CHAIN_OFFSETS = {
    "speech_ended": 0.0,
    "segment_closed": 0.69,
    "transcription_started": 0.75,
    "transcript_written": 1.8,
    "wake_read": 1.95,
    "decision_started": 1.98,
    "decision_done": 2.4,
    "prompt_sent": 2.46,
    "prompt_delivered": 2.55,
    "agent_first_command": 6.0,
    "reply_invoked": 9.5,
    "speech_received": 9.8,
    "synthesis_started": 9.81,
    "synthesized": 10.6,
    "first_audio": 10.65,
}


def at(offset):
    return HEARD_AT + offset


def acknowledged(**timing_offsets):
    timing = {key: round(at(offset) * 1000) for key, offset in timing_offsets.items()}
    return voice_turns.speech_moments({"timing": timing})


class RecordingClock:
    def __init__(self, monkeypatch):
        self.at = HEARD_AT
        self.lines = []
        monkeypatch.setattr(transcript_log, "datetime", self)

    def now(self, zone):
        return datetime.fromtimestamp(self.at, zone)

    def record(self, offset, recorder, *arguments, **details):
        self.at = at(offset)
        recorder(self.lines.append, *arguments, **details)


def heard_entry(sequence, text):
    return {
        "sequence": sequence,
        "text": text,
        "source": "human",
        "speaker": None,
        "turn_finished": True,
        "speech_ended": at(0.0),
        "segment_closed": at(0.69),
        "transcription_started": at(0.75),
        "time": at(1.8),
    }


def switched_to_the_target(clock):
    clock.record(1.95, transcript_log.report_conversation, heard_entry(80, "hey"))
    clock.record(
        2.4,
        transcript_log.report_addressing,
        CONVERSATION,
        sequence=80,
        candidates=["Ibaraki"],
        latency_ms=420,
        verdict="candidate",
        choice="Ibaraki",
        confidence=0.99,
    )
    clock.lines.append(f"wake Ibaraki-dōji at {TARGET}")
    clock.record(
        2.55,
        transcript_log.report_delivery,
        purpose=CONVERSATION,
        sequence=80,
        servant="Ibaraki-dōji",
        pane=TARGET,
        host=None,
        delivered="prompt",
        delivery_ms=90,
    )


def replied_after_an_interrupted_attempt(clock):
    clock.record(3.0, transcript_log.report_talk, "follow", OTHER_PANE)
    clock.record(6.0, transcript_log.report_talk, "follow", TARGET)
    clock.record(8.0, transcript_log.report_talk, "say", TARGET)
    clock.record(
        9.1,
        transcript_log.report_speech,
        TARGET,
        invoked=at(8.0),
        status="interrupted",
        source="elevenlabs",
        **acknowledged(received=8.3, synthesisStarted=8.3, synthesized=9.0),
    )
    clock.record(9.5, transcript_log.report_talk, "say", TARGET)
    clock.record(
        14.0,
        transcript_log.report_speech,
        TARGET,
        invoked=at(9.5),
        status="finished",
        source="elevenlabs",
        **acknowledged(
            received=9.8, synthesisStarted=9.81, synthesized=10.6, playing=10.65
        ),
    )
