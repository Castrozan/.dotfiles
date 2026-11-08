import dataclasses
import difflib
import re
import unicodedata

GREETINGS = frozenset(
    {"hey", "hei", "hi", "ok", "okay", "ei", "oi", "ola", "ai", "o", "e", "em"}
)
NAME_SIMILARITY = 0.75
WORD = re.compile(r"[^\W_]+")
MESSAGE_EDGE = " ,.;:!?-"


@dataclasses.dataclass(frozen=True)
class LiveSession:
    servant: str
    pane: str


@dataclasses.dataclass(frozen=True)
class WakeMatch:
    session: LiveSession
    message: str


def folded(text):
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )


def spoken_name(servant):
    return folded(WORD.findall(servant)[0])


def similarity(first, second):
    return difflib.SequenceMatcher(None, first, second).ratio()


def sessions_by_spoken_name(sessions):
    grouped = {}
    for session in sessions:
        grouped.setdefault(spoken_name(session.servant), []).append(session)
    return {name: group[0] for name, group in grouped.items() if len(group) == 1}


def named_session(word, candidates):
    scored = sorted(
        ((similarity(word, name), name) for name in candidates), reverse=True
    )
    if not scored or scored[0][0] < NAME_SIMILARITY:
        return None
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None
    return candidates[scored[0][1]]


def opens_with_greeting(text):
    first = WORD.search(text)
    return first is not None and folded(first.group()) in GREETINGS


def addressed_session(text, sessions):
    words = list(WORD.finditer(text))
    candidates = sessions_by_spoken_name(sessions)
    greetings = 0
    while greetings < len(words) and folded(words[greetings].group()) in GREETINGS:
        greetings += 1
    if not greetings or greetings == len(words):
        return None
    name = words[greetings]
    session = named_session(folded(name.group()), candidates)
    if session is None:
        return None
    return WakeMatch(session, text[name.end() :].strip(MESSAGE_EDGE))
