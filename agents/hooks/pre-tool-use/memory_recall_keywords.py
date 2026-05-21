from __future__ import annotations

import re

MAX_KEYWORDS = 20
MIN_KEYWORD_LENGTH = 3


ENGLISH_STOP_WORDS = {
    "the",
    "and",
    "for",
    "are",
    "with",
    "this",
    "that",
    "from",
    "have",
    "has",
    "had",
    "was",
    "were",
    "but",
    "not",
    "you",
    "your",
    "all",
    "any",
    "can",
    "will",
    "would",
    "should",
    "could",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "how",
    "into",
    "out",
    "out",
    "did",
    "do",
    "does",
    "done",
    "get",
    "got",
    "let",
    "use",
    "used",
    "than",
    "then",
    "there",
    "these",
    "those",
    "they",
    "them",
    "their",
    "its",
    "it",
    "is",
    "as",
    "at",
    "by",
    "of",
    "on",
    "in",
    "to",
    "or",
    "be",
    "an",
    "if",
    "we",
    "he",
    "she",
    "i",
    "me",
    "my",
    "mine",
    "our",
}

PORTUGUESE_STOP_WORDS = {
    "para",
    "com",
    "uma",
    "isso",
    "esse",
    "essa",
    "isto",
    "este",
    "esta",
    "voce",
    "você",
    "como",
    "quando",
    "onde",
    "porque",
    "porquê",
    "por",
    "que",
    "qual",
    "quais",
    "tem",
    "tinha",
    "foi",
    "fui",
    "sao",
    "são",
    "era",
    "ser",
    "tem",
    "ter",
    "fez",
    "faz",
    "fazer",
    "vai",
    "vou",
    "vamos",
    "nao",
    "não",
    "sim",
    "mas",
    "ou",
    "se",
    "o",
    "a",
    "os",
    "as",
    "um",
    "uma",
    "do",
    "da",
    "dos",
    "das",
    "no",
    "na",
    "nos",
    "nas",
    "ao",
    "aos",
    "à",
    "às",
    "eu",
    "ele",
    "ela",
    "nos",
    "nós",
}

ALL_STOP_WORDS = ENGLISH_STOP_WORDS | PORTUGUESE_STOP_WORDS


def collect_strings_from_tool_input(tool_input) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if isinstance(tool_input, dict):
        return " ".join(
            collect_strings_from_tool_input(value) for value in tool_input.values()
        )
    if isinstance(tool_input, list):
        return " ".join(collect_strings_from_tool_input(item) for item in tool_input)
    return ""


def extract_keywords_from_text(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9_À-ſ]+", text.lower())
    keywords: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if len(token) < MIN_KEYWORD_LENGTH:
            continue
        if token in ALL_STOP_WORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= MAX_KEYWORDS:
            break
    return keywords
