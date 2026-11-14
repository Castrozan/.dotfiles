import difflib
import re

from transcription import ordinary_words

SPELLED_ALIKE = 2.0
SHORT_KEY_LENGTH = 4
MEDIUM_KEY_LENGTH = 5
SHORT_NAME_SIMILARITY = 1.0
MEDIUM_NAME_SIMILARITY = 0.8
LONG_NAME_SIMILARITY = 0.72
SHORTEST_JOINED_WORD = 3
REPEATED_SOUND = re.compile(r"(.)\1+")
SOUND_RULES = (
    ("sch", "S"),
    ("sh", "S"),
    ("ch", "S"),
    ("x", "S"),
    ("ph", "f"),
    ("ce", "se"),
    ("ci", "si"),
    ("c", "k"),
    ("q", "k"),
    ("y", "i"),
    ("z", "s"),
    ("h", ""),
)


def sound_key(word):
    for spelling, sound in SOUND_RULES:
        word = word.replace(spelling, sound)
    return REPEATED_SOUND.sub(r"\1", word)


def ordinary_vocabulary():
    return ordinary_words.frequency_ranks()


def required_similarity(name_key):
    if len(name_key) <= SHORT_KEY_LENGTH:
        return SHORT_NAME_SIMILARITY
    if len(name_key) == MEDIUM_KEY_LENGTH:
        return MEDIUM_NAME_SIMILARITY
    return LONG_NAME_SIMILARITY


def joins_fragments(words):
    return len(words) > 1 and any(len(word) < SHORTEST_JOINED_WORD for word in words)


def holds_an_ordinary_word(words, vocabulary):
    return vocabulary is None or any(word in vocabulary for word in words)


def sounds_alike(heard_key, name_key):
    return heard_key == name_key and len(name_key) > SHORT_KEY_LENGTH


def sounded_similarity(words, heard_key, name_key, vocabulary):
    if holds_an_ordinary_word(words, vocabulary) and not sounds_alike(
        heard_key, name_key
    ):
        return None
    similarity = difflib.SequenceMatcher(None, heard_key, name_key).ratio()
    return similarity if similarity >= required_similarity(name_key) else None


def heard_similarity(words, name, vocabulary):
    if joins_fragments(words):
        return None
    heard = "".join(words)
    if heard == name:
        return SPELLED_ALIKE
    return sounded_similarity(words, sound_key(heard), sound_key(name), vocabulary)


def heard_name(windows, names, vocabulary):
    heard = [
        (similarity, name, len(words))
        for words in windows
        for name in names
        if (similarity := heard_similarity(words, name, vocabulary)) is not None
    ]
    if not heard:
        return None
    clearest = max(similarity for similarity, _, _ in heard)
    leaders = [
        (name, size) for similarity, name, size in heard if similarity == clearest
    ]
    if len({name for name, _ in leaders}) > 1:
        return None
    return min(leaders, key=lambda leader: leader[1])
