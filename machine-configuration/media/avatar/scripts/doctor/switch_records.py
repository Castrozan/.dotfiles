import dataclasses
import itertools
import json
import math
from datetime import datetime

CONVERSATION = "conversation"


@dataclasses.dataclass(frozen=True)
class Logged:
    at: float
    record: dict


def parsed(line):
    if not line.startswith("{"):
        return None
    try:
        record = json.loads(line)
    except ValueError:
        return None
    return record if isinstance(record, dict) and "timestamp" in record else None


def logged_records(lines):
    records = filter(None, map(parsed, lines))
    logged = [
        Logged(datetime.fromisoformat(record["timestamp"]).timestamp(), record)
        for record in records
    ]
    return sorted(logged, key=lambda item: item.at)


def is_delivery(record):
    return record.get("phase") == "delivery"


def is_switch_decision(record):
    return (
        record.get("decision") == "addressing"
        and record.get("phase") == CONVERSATION
        and record.get("verdict") == "candidate"
    )


def is_conversation_switch(record):
    return is_switch_decision(record) or record.get("purpose") == CONVERSATION


def heard_as(sequence):
    return lambda record: (
        record.get("phase") == CONVERSATION
        and "text" in record
        and record.get("sequence") == sequence
    )


def decided_on(sequence):
    return lambda record: (
        record.get("decision") == "addressing" and record.get("sequence") == sequence
    )


def talk_from(pane):
    return lambda record: record.get("phase") == "talk" and record.get("pane") == pane


def reply_from(pane, delivered, tenure_end):
    return lambda record: (
        record.get("phase") == "speech"
        and record.get("pane") == pane
        and record.get("playing") is not None
        and delivered <= record.get("invoked", -math.inf) < tenure_end
    )


def latest(logged, start, index, wanted):
    return next(
        (
            logged[position]
            for position in range(index, start - 1, -1)
            if wanted(logged[position].record)
        ),
        None,
    )


def first_after(logged, index, until, wanted):
    following = itertools.takewhile(
        lambda item: item.at < until, itertools.islice(logged, index + 1, None)
    )
    return next((item for item in following if wanted(item.record)), None)
