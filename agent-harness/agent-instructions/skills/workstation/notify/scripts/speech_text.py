import html
import re
import unicodedata


SENSITIVE_TEXT = re.compile(
    r"(?i)(?:\b(?:password|passphrase|secret|bearer|authorization|credential|"
    r"(?:api|access|refresh|session|id)[_ -]?(?:key|token)|token)\b|"
    r"-----BEGIN [^-]*PRIVATE KEY|\b(?:sk|ghp|gho|ghu|ghs|ghr)[-_][A-Za-z0-9]|"
    r"\bAKIA[A-Z0-9]{16}\b|\beyJ[A-Za-z0-9_-]+\.|[A-Za-z0-9_+/=-]{32,})"
)


SPOKEN_PUNCTUATION = (
    (">=", " greater than or equal to "),
    ("<=", " less than or equal to "),
    (">", " greater than "),
    ("<", " less than "),
    ("&", " and "),
    ("%", " percent "),
)


def replace_punctuation_with_words(text: str) -> str:
    for punctuation, words in SPOKEN_PUNCTUATION:
        text = text.replace(punctuation, words)
    return text


def keep_speakable_characters(text: str) -> str:
    return "".join(
        character if character.isalnum() or character in ".,!?;: " else " "
        for character in text
    )


def sanitize_speech(message: str) -> str | None:
    text = unicodedata.normalize("NFKC", html.unescape(message))
    if SENSITIVE_TEXT.search(text):
        return None
    text = re.sub(r"(?m)^[ \t]*(?:`{3,}|~{3,})[^\n]*$", " ", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+|\b\S+@\S+\b", " ", text)
    text = re.sub(r"<(?=[A-Za-z/!])[^>]*>", " ", text)
    text = re.sub(r"(?<=\d)/(?=\d)", " out of ", text)
    text = replace_punctuation_with_words(text)
    text = re.sub(r"(?<=\d)-(?=\d)", " to ", text)
    text = re.sub(r"(?<!\w)-(?=\d)", "minus ", text)
    text = re.sub(r"(?<=\w)\.(?=[A-Za-z])", " ", text)
    text = keep_speakable_characters(text)
    text = re.sub(r"\s+", " ", text).strip(" .,!?;:")
    return text if any(character.isalnum() for character in text) else None
