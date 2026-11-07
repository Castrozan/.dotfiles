import re
from dataclasses import dataclass

MAXIMUM_SENTENCE_WORDS = 40
ADVISED_SENTENCE_WORDS = 25
SENTENCE_BOUNDARY = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z0-9\"'(`])|(?<=[;:])\s+(?=\d+\)\s)|^\s*(?=\d+\)\s)"
)


@dataclass(frozen=True)
class SentenceLength:
    line_number: int
    word_count: int


def inspect_sentence_lengths(token, first_line_number, inspection):
    for sentence in sentence_lengths(token, first_line_number):
        if sentence.word_count > MAXIMUM_SENTENCE_WORDS:
            inspection.reject(
                "instruction_sentence_word_limit",
                sentence.line_number,
                f"expected at most {MAXIMUM_SENTENCE_WORDS} words per sentence, found {sentence.word_count}",
            )
        elif sentence.word_count > ADVISED_SENTENCE_WORDS:
            inspection.warn(
                "instruction_sentence_word_advice",
                sentence.line_number,
                f"sentence has {sentence.word_count} words; when writing or rewriting it, reword it to "
                f"{ADVISED_SENTENCE_WORDS} words or fewer, because longer sentences are a bad practice",
            )


def sentence_lengths(token, first_line_number):
    prose = "".join(_prose_text(child) for child in token.children or [])
    starts = sorted(
        {0} | {boundary.end() for boundary in SENTENCE_BOUNDARY.finditer(prose)}
    )
    ends = starts[1:] + [len(prose)]
    return [
        SentenceLength(
            first_line_number + prose.count("\n", 0, start),
            len(prose[start:end].split()),
        )
        for start, end in zip(starts, ends, strict=True)
        if prose[start:end].strip()
    ]


def _prose_text(child):
    if child.type == "softbreak":
        return "\n"
    if child.type == "code_inline":
        return "`literal`"
    return child.content
