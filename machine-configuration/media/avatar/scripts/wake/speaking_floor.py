import dataclasses

import conversation_addressee
import transcript_log
from conversation_addressee import Addressee
from wake_phrase import vocative_session

TRANSCRIPT_FILE = "transcript.jsonl"
AVATAR_SPEAKER = "avatar"


@dataclasses.dataclass(frozen=True)
class FloorBoundaries:
    sessions: object
    listening: object


def latest_named(entries, sessions):
    for entry in reversed(entries):
        if entry.get("speaker") == AVATAR_SPEAKER:
            continue
        session = vocative_session(entry["text"], sessions)
        if session:
            return Addressee(session.pane, session.servant, entry["sequence"])
    return None


def first_claim(pane, sessions, holder):
    claimer = next((session for session in sessions if session.pane == pane), None)
    if claimer is None:
        return None
    return Addressee(pane, claimer.servant, holder.heard_through if holder else 0)


def settle(holder, named, pane, sessions):
    if named and (holder is None or named.pane != holder.pane):
        return named
    if holder and any(session.pane == holder.pane for session in sessions):
        return holder
    return first_claim(pane, sessions, holder)


def claim(directory, pane, boundaries):
    with conversation_addressee.exclusive(directory):
        holder = conversation_addressee.current(directory)
        entries = transcript_log.read_since(
            directory / TRANSCRIPT_FILE, holder.heard_through if holder else 0
        )
        if holder and holder.pane == pane and not entries:
            return holder
        if not boundaries.listening():
            return None
        sessions = boundaries.sessions()
        settled = settle(holder, latest_named(entries, sessions), pane, sessions)
        if settled and settled != holder:
            conversation_addressee.write(directory, settled)
        return settled


def may_speak(holder, pane):
    return holder is None or holder.pane == pane
