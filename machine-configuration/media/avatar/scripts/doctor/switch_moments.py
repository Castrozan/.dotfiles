import dataclasses
import itertools
import math

from switch_records import (
    decided_on,
    first_after,
    heard_as,
    is_conversation_switch,
    is_delivery,
    is_switch_decision,
    latest,
    reply_from,
    talk_from,
)

LONGEST_SPEECH_SECONDS = 310
BOUNDARIES = (
    "speech_ended",
    "segment_closed",
    "transcription_started",
    "transcript_written",
    "wake_read",
    "decision_started",
    "decision_done",
    "prompt_sent",
    "prompt_delivered",
    "agent_first_command",
    "reply_invoked",
    "speech_received",
    "synthesis_started",
    "synthesized",
    "first_audio",
)
HEARD_MOMENTS = (
    "speech_ended",
    "segment_closed",
    "transcription_started",
    "transcript_written",
)
SPEECH_MOMENTS = {
    "reply_invoked": "invoked",
    "speech_received": "speech_received",
    "synthesis_started": "synthesis_started",
    "synthesized": "synthesized",
    "first_audio": "playing",
}


@dataclasses.dataclass(frozen=True)
class Switch:
    switched_at: float
    servant: str
    pane: str | None
    sequence: int
    delivered: str | None
    moments: dict


def heard_moments(heard):
    if heard is None:
        return {}
    return {name: heard.record.get(name) for name in HEARD_MOMENTS} | {
        "wake_read": heard.at
    }


def decision_moments(decision):
    if decision is None:
        return {}
    started = decision.at - decision.record["latency_ms"] / 1000
    return {"decision_started": started, "decision_done": decision.at}


def delivery_moments(anchor):
    if not is_delivery(anchor.record):
        return {}
    sent = anchor.at - anchor.record["delivery_ms"] / 1000
    return {"prompt_sent": sent, "prompt_delivered": anchor.at}


def reply_moments(reply):
    if reply is None:
        return {}
    return {name: reply.record.get(key) for name, key in SPEECH_MOMENTS.items()}


def agent_moments(logged, index, tenure_end):
    anchor = logged[index]
    if not is_delivery(anchor.record):
        return {}
    pane = anchor.record.get("pane")
    command = first_after(logged, index, tenure_end, talk_from(pane))
    reply = first_after(
        logged,
        index,
        tenure_end + LONGEST_SPEECH_SECONDS,
        reply_from(pane, anchor.at, tenure_end),
    )
    first_command = {"agent_first_command": command.at} if command else {}
    return first_command | reply_moments(reply)


def measured(logged, start, index, tenure_end):
    anchor = logged[index]
    sequence = anchor.record.get("sequence")
    moments = (
        heard_moments(latest(logged, start, index - 1, heard_as(sequence)))
        | decision_moments(latest(logged, start, index, decided_on(sequence)))
        | delivery_moments(anchor)
        | agent_moments(logged, index, tenure_end)
    )
    return Switch(
        switched_at=moments.get("decision_done") or anchor.at,
        servant=anchor.record.get("servant") or anchor.record.get("choice"),
        pane=anchor.record.get("pane"),
        sequence=sequence,
        delivered=anchor.record.get("delivered"),
        moments={name: moments.get(name) for name in BOUNDARIES},
    )


def delivered_next(logged, index, next_index):
    decision = logged[index].record
    if next_index is None or not is_switch_decision(decision):
        return False
    upcoming = logged[next_index].record
    return is_delivery(upcoming) and upcoming.get("sequence") == decision["sequence"]


def switch_positions(logged):
    anchors = [
        index
        for index, item in enumerate(logged)
        if is_delivery(item.record) or is_switch_decision(item.record)
    ]
    return [
        index
        for index, next_index in itertools.pairwise([*anchors, None])
        if not delivered_next(logged, index, next_index)
    ]


def tenure_end(logged, next_index):
    return math.inf if next_index is None else logged[next_index].at


def switches_in(logged):
    positions = switch_positions(logged)
    tenures = zip([0, *positions], positions, [*positions[1:], None], strict=False)
    return [
        measured(logged, start, index, tenure_end(logged, next_index))
        for start, index, next_index in tenures
        if is_conversation_switch(logged[index].record)
    ]
