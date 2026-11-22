import collections
import dataclasses

import addressing_decision
import transcript_log
from addressing_decision import Route, Turn
from conversation_seat import Seat
from transcription.spoken_names import called_name
from wake_phrase import (
    MESSAGE_EDGE,
    WakeMatch,
    addressed_session,
    opens_with_greeting,
    sessions_heard_anywhere,
)

CONTEXT_TURNS = 6
MICROPHONE_SOURCE = "human"
WAKE_PHASE = "wake"
CONVERSATION_PHASE = "conversation"
DECISION_UNAVAILABLE = (OSError, ValueError)


@dataclasses.dataclass(frozen=True)
class Utterance:
    phase: str
    text: str
    sequence: int | None = None
    holder: object = None
    context: tuple = ()


def holds_the_floor(holder, session):
    return bool(holder) and (holder.pane, holder.host) == (session.pane, session.host)


def by_called_name(sessions):
    return {called_name(session.servant): session for session in sessions}


def from_the_microphone(entry):
    return entry.get("source") == MICROPHONE_SOURCE


def unavailable_because(error):
    return str(error) or type(error).__name__


class VoiceAddressing:
    def __init__(self, boundaries, known_sessions, refreshed_sessions):
        self.boundaries = boundaries
        self.known_sessions = known_sessions
        self.refreshed_sessions = refreshed_sessions
        self.recent_turns = collections.deque(maxlen=CONTEXT_TURNS)

    def forget_turns(self):
        self.recent_turns.clear()

    def live_sessions_named(self, text):
        if opens_with_greeting(text) or sessions_heard_anywhere(
            text, self.known_sessions()
        ):
            return sessions_heard_anywhere(text, self.refreshed_sessions())
        return []

    def wake_match(self, heard):
        named = by_called_name(self.live_sessions_named(heard))
        if not named:
            self.boundaries.report("Ignored wake: no unique live servant named")
            return None
        verdict = self.decided(Utterance(WAKE_PHASE, heard), named)
        if verdict is None:
            return self.greeted_at_the_wake(heard)
        match = self.chosen(verdict, named, heard)
        if match is None:
            self.boundaries.report("Ignored wake: no live servant addressed")
        return match

    def greeted_at_the_wake(self, heard):
        if not opens_with_greeting(heard):
            self.boundaries.report("Ignored wake: no opening greeting")
            return None
        match = addressed_session(heard, self.refreshed_sessions())
        if match is None:
            self.boundaries.report("Ignored wake: no unique live servant")
        return match

    def conversation_match(self, entry):
        if not from_the_microphone(entry):
            return self.greeted_in_conversation(
                entry["text"], self.boundaries.addressee
            )
        named = self.live_sessions_named(entry["text"])
        match = self.turned_to(entry, named) if named else None
        self.recent_turns.append(Turn(entry.get("speaker"), entry["text"]))
        return match

    def turned_to(self, entry, named):
        holder = self.boundaries.addressee()
        candidates = by_called_name(
            session for session in named if not holds_the_floor(holder, session)
        )
        if not candidates:
            return None
        if self.boundaries.open_seat() == Seat.DISCORD:
            return self.greeted_in_conversation(entry["text"], lambda: holder)
        utterance = Utterance(
            CONVERSATION_PHASE,
            entry["text"],
            entry["sequence"],
            holder,
            tuple(self.recent_turns),
        )
        return self.decided_or_greeted(utterance, candidates)

    def decided_or_greeted(self, utterance, candidates):
        verdict = self.decided(utterance, candidates)
        if verdict is None:
            return self.greeted_in_conversation(
                utterance.text, lambda: utterance.holder
            )
        return self.chosen(verdict, candidates, utterance.text)

    def greeted_in_conversation(self, text, holder_of):
        if not opens_with_greeting(text):
            return None
        match = addressed_session(text, self.refreshed_sessions())
        if match is None or holds_the_floor(holder_of(), match.session):
            return None
        return match

    def decided(self, utterance, candidates):
        names = list(candidates)
        holder = called_name(utterance.holder.servant) if utterance.holder else None
        input_messages, questions = addressing_decision.request(
            utterance.text, utterance.context, holder, names
        )
        started = self.boundaries.now()
        try:
            answers = self.boundaries.decide(input_messages, questions)
        except DECISION_UNAVAILABLE as error:
            self.report(utterance, names, started, fallback=unavailable_because(error))
            return None
        verdict = addressing_decision.verdict(answers, names)
        self.report(
            utterance,
            names,
            started,
            verdict=verdict.route,
            choice=verdict.choice,
            confidence=verdict.confidence,
        )
        return verdict

    def report(self, utterance, names, started, **outcome):
        transcript_log.report_addressing(
            self.boundaries.report,
            utterance.phase,
            sequence=utterance.sequence,
            candidates=names,
            latency_ms=round((self.boundaries.now() - started) * 1000),
            **outcome,
        )

    def chosen(self, verdict, candidates, text):
        if verdict.route is not Route.CANDIDATE:
            return None
        session = candidates[verdict.choice]
        if session not in self.refreshed_sessions():
            self.boundaries.report(f"Kept the route: {session.servant} left")
            return None
        return WakeMatch(session, text.strip(MESSAGE_EDGE))
