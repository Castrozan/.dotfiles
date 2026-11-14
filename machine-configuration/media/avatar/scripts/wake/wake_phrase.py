import dataclasses

import name_hearing
from transcription.ordinary_words import folded
from transcription.spoken_names import WORD, answered_names, called_name

GREETINGS = frozenset(
    {"hey", "hei", "hi", "ok", "okay", "ei", "oi", "ola", "ai", "o", "e", "em"}
)
MESSAGE_EDGE = " ,.;:!?-"
WINDOW_SIZES = (1, 2, 3)


@dataclasses.dataclass(frozen=True)
class LiveSession:
    servant: str
    pane: str


@dataclasses.dataclass(frozen=True)
class WakeMatch:
    session: LiveSession
    message: str


def spoken_name(servant):
    return folded(called_name(servant))


def spoken_names_of(servant):
    return dict.fromkeys(folded(name) for name in answered_names(servant))


def sessions_by_spoken_name(sessions):
    grouped = {}
    for session in sessions:
        for name in spoken_names_of(session.servant):
            grouped.setdefault(name, []).append(session)
    return {name: group[0] for name, group in grouped.items() if len(group) == 1}


def leading_windows(texts, start):
    return [
        tuple(texts[start : start + size])
        for size in WINDOW_SIZES
        if start + size <= len(texts)
    ]


def trailing_windows(texts, floor):
    return [
        tuple(texts[len(texts) - size :])
        for size in WINDOW_SIZES
        if len(texts) - size >= floor
    ]


def leading_greetings(words):
    count = 0
    while count < len(words) and folded(words[count].group()) in GREETINGS:
        count += 1
    return count


def opens_with_greeting(text):
    first = WORD.search(text)
    return first is not None and folded(first.group()) in GREETINGS


def heard_among(windows, candidates):
    return name_hearing.heard_name(
        windows, candidates, name_hearing.ordinary_vocabulary()
    )


def vocative_session(text, sessions):
    words = list(WORD.finditer(text))
    greetings = leading_greetings(words)
    if greetings == len(words):
        return None
    texts = [folded(word.group()) for word in words]
    windows = leading_windows(texts, greetings) + trailing_windows(texts, greetings)
    candidates = sessions_by_spoken_name(sessions)
    heard = heard_among(windows, candidates)
    return candidates[heard[0]] if heard else None


def addressed_session(text, sessions):
    words = list(WORD.finditer(text))
    greetings = leading_greetings(words)
    if not greetings or greetings == len(words):
        return None
    texts = [folded(word.group()) for word in words]
    candidates = sessions_by_spoken_name(sessions)
    heard = heard_among(leading_windows(texts, greetings), candidates)
    if heard is None:
        return None
    name, size = heard
    return WakeMatch(
        candidates[name], text[words[greetings + size - 1].end() :].strip(MESSAGE_EDGE)
    )


def named_in_turn(text, sessions):
    match = addressed_session(text, sessions)
    if match:
        return match
    session = vocative_session(text, sessions)
    return WakeMatch(session, text.strip(MESSAGE_EDGE)) if session else None
