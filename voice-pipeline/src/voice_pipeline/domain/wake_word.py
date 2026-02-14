import re


class WakeWordDetector:
    def __init__(self, wake_words: list[str]) -> None:
        self._wake_words = [w.lower() for w in wake_words]
        escaped = [re.escape(w) for w in self._wake_words]
        self._pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

    @property
    def wake_words(self) -> list[str]:
        return list(self._wake_words)

    def detect(self, transcript: str) -> str | None:
        match = self._pattern.search(transcript)
        if match:
            return match.group(1).lower()
        return None

    def extract_post_wake_word_text(self, transcript: str) -> str:
        match = self._pattern.search(transcript)
        if not match:
            return transcript
        return transcript[match.end():].strip()
