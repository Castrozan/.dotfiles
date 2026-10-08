import html
import re
import unicodedata


SENSITIVE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:password|passphrase|secret|bearer|authorization|credential|token)\b"
    ),
    re.compile(r"(?i)\b(?:api|access|refresh|session|id)[_ -]?(?:key|token)\b"),
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY"),
    re.compile(r"\b(?:sk|ghp|gho|ghu|ghs|ghr)[-_][A-Za-z0-9]"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\."),
    re.compile(r"[A-Za-z0-9_+/=-]{32,}"),
)


CODE_FENCE_MARKERS = ("```", "~~~")

SPOKEN_PUNCTUATION = (
    (">=", " greater than or equal to "),
    ("<=", " less than or equal to "),
    (">", " greater than "),
    ("<", " less than "),
    ("&", " and "),
    ("%", " percent "),
)


def contains_sensitive_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)


def replace_punctuation_with_words(text: str) -> str:
    for punctuation, words in SPOKEN_PUNCTUATION:
        text = text.replace(punctuation, words)
    return text


def blank_code_fence_lines(text: str) -> str:
    return "\n".join(
        " " if line.lstrip(" \t").startswith(CODE_FENCE_MARKERS) else line
        for line in text.split("\n")
    )


def keep_speakable_characters(text: str) -> str:
    return "".join(
        character if character.isalnum() or character in ".,!?;: " else " "
        for character in text
    )


def sanitize_speech(message: str) -> str | None:
    text = unicodedata.normalize("NFKC", html.unescape(message))
    if contains_sensitive_text(text):
        return None
    text = blank_code_fence_lines(text)
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
