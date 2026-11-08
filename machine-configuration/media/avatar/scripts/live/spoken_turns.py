import enum
from dataclasses import dataclass


class Party(enum.StrEnum):
    HUMAN = "human"
    AVATAR = "avatar"


@dataclass(frozen=True)
class SpokenTurn:
    party: Party
    text: str


class TurnAssembler:
    def __init__(self, settle_seconds):
        self.settle_seconds = settle_seconds
        self.party = None
        self.words = ""
        self.last_heard_at = None

    def add(self, party, text, now):
        finished = self.finish() if party != self.party else []
        self.party = party
        self.words += text
        self.last_heard_at = now
        return finished

    def settled(self, now):
        if self.party is None or now - self.last_heard_at < self.settle_seconds:
            return []
        return self.finish()

    def finish(self):
        party, text = self.party, self.words.strip()
        self.party, self.words, self.last_heard_at = None, "", None
        return [SpokenTurn(party, text)] if party and text else []
