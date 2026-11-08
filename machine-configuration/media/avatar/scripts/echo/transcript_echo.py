import collections
import difflib
import re

WINDOW_SECONDS = 15
SIMILARITY_RATIO = 0.75
MINIMUM_CONTAINED_WORDS = 3
NON_WORD = re.compile(r"[^\w\s]")


def normalized(text):
    return " ".join(NON_WORD.sub("", text.lower()).split())


def resembles(first, second):
    if difflib.SequenceMatcher(None, first, second).ratio() >= SIMILARITY_RATIO:
        return True
    shorter, longer = sorted((first, second), key=len)
    return len(shorter.split()) >= MINIMUM_CONTAINED_WORDS and shorter in longer


class EchoFilter:
    def __init__(self):
        self.recent = collections.deque()

    def forget_expired(self, now):
        while self.recent and now - self.recent[0][0] > WINDOW_SECONDS:
            self.recent.popleft()

    def heard_elsewhere(self, source, words):
        return any(
            other != source and resembles(words, earlier)
            for _, other, earlier in self.recent
        )

    def is_echo(self, source, text, now):
        self.forget_expired(now)
        words = normalized(text)
        if self.heard_elsewhere(source, words):
            return True
        self.recent.append((now, source, words))
        return False
