import json
from itertools import accumulate

from control_server_node_runner import (
    CONTROL_SERVER_DIRECTORY,
    evaluate_node_json,
    requires_node,
)
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

FUNCTION_WORDS = json.loads(
    (CONTROL_SERVER_DIRECTORY / "speech" / "language-function-words.json").read_text()
)
ANY_TEXT = st.text(st.characters(exclude_categories=["Cs"]), min_size=1, max_size=700)
UNDECIDABLE_WORD = st.text("bcdfghjklmnpqrstvwxz", min_size=1, max_size=12)
LONGEST_PHRASE = 8 * 12 + 7 + 2
EXAMPLES = settings(max_examples=40, deadline=None)


def phrase(word, ending, capitalized=True):
    joined = st.lists(word, min_size=1, max_size=8).map(" ".join)
    return st.tuples(joined.map(str.capitalize) if capitalized else joined, ending).map(
        "".join
    )


SENTENCE_ENDINGS = st.sampled_from([". ", "! ", "? "])
SENTENCES = st.lists(
    phrase(UNDECIDABLE_WORD, SENTENCE_ENDINGS), min_size=1, max_size=12
)
CLAUSES = st.lists(
    phrase(UNDECIDABLE_WORD, st.sampled_from([", ", "; ", ": "]), capitalized=False),
    min_size=2,
    max_size=12,
)
LABELLED_SENTENCES = st.lists(
    st.one_of(
        *[
            phrase(st.sampled_from(FUNCTION_WORDS[language]), SENTENCE_ENDINGS).map(
                lambda sentence, language=language: (language, sentence)
            )
            for language in ("pt-br", "en-us")
        ],
        phrase(UNDECIDABLE_WORD, SENTENCE_ENDINGS).map(lambda s: ("undecided", s)),
        st.text("あいうえおかきくけこさしすせそ", min_size=1, max_size=30).map(
            lambda sentence: ("other", sentence + "。")
        ),
    ),
    min_size=1,
    max_size=12,
)


def chunks_of(texts, maximum):
    code_points = evaluate_node_json(
        f"""
        const {{ speechChunks }} = require("./speech/speech-chunks");
        const result = {json.dumps(texts)}.map((text) =>
          speechChunks(text, {maximum}).map((chunk) =>
            Array.from(chunk, (character) => character.codePointAt(0)),
          ),
        );
        """
    )
    return [["".join(map(chr, chunk)) for chunk in chunks] for chunks in code_points]


def chunk_languages(text, maximum):
    return evaluate_node_json(
        f"""
        const {{ speechChunks }} = require("./speech/speech-chunks");
        const {{ spokenLanguageOf }} = require("./speech/spoken-language");
        const result = speechChunks({json.dumps(text)}, {maximum}).map((chunk) => [
          chunk, spokenLanguageOf(chunk, "pt-br"), spokenLanguageOf(chunk, "en-us"),
        ]);
        """
    )


def spoken_length(text):
    return len(text.encode("utf-16-le")) // 2


def ends_of(pieces):
    return set(accumulate(map(len, pieces)))


def expected_language(labels):
    decided = labels - {"undecided"}
    if not decided:
        return ["pt-br", "en-us"]
    (language,) = decided
    return [None, None] if language == "other" else [language, language]


@requires_node
@EXAMPLES
@given(
    texts=st.lists(ANY_TEXT, min_size=1, max_size=6),
    maximum=st.integers(min_value=2, max_value=240),
)
@example(texts=["\x85"], maximum=2)
def test_any_text_splits_into_bounded_chunks_that_rebuild_it(texts, maximum):
    for text, chunks in zip(texts, chunks_of(texts, maximum), strict=True):
        assert "".join(chunks) == text
        assert all(0 < spoken_length(chunk) <= maximum for chunk in chunks)


@requires_node
@EXAMPLES
@given(sentences=SENTENCES, maximum=st.integers(LONGEST_PHRASE, 240))
def test_sentences_that_fit_stay_whole_and_fill_each_chunk(sentences, maximum):
    (chunks,) = chunks_of(["".join(sentences)], maximum)
    sentence_starting_at = dict(
        zip(accumulate(map(len, sentences), initial=0), sentences, strict=False)
    )
    assert ends_of(chunks) <= ends_of(sentences)
    for end, chunk in zip(accumulate(map(len, chunks[:-1])), chunks, strict=False):
        assert len(chunk) + len(sentence_starting_at[end]) > maximum


@requires_node
@EXAMPLES
@given(clauses=CLAUSES, maximum=st.integers(LONGEST_PHRASE, 200))
def test_a_sentence_too_long_to_fit_breaks_only_after_its_clauses(clauses, maximum):
    sentence = "".join(clauses).capitalize().rstrip(",;: ") + "."
    assume(len(sentence) > maximum)
    (chunks,) = chunks_of([sentence], maximum)
    assert ends_of(chunks[:-1]) <= ends_of(clauses[:-1])


@requires_node
@EXAMPLES
@given(labelled=LABELLED_SENTENCES, maximum=st.integers(LONGEST_PHRASE, 240))
def test_every_chunk_is_heard_in_the_language_of_each_sentence_in_it(labelled, maximum):
    sentences = [sentence for _, sentence in labelled]
    chunks = chunk_languages("".join(sentences), maximum)
    assert ends_of([chunk for chunk, *_ in chunks]) <= ends_of(sentences)
    sentence_ends = list(accumulate(map(len, sentences)))
    start = 0
    for chunk, *heard_as in chunks:
        end = start + len(chunk)
        labels = {
            label
            for (label, _), sentence_end in zip(labelled, sentence_ends, strict=True)
            if start < sentence_end <= end
        }
        assert not ({"other"} < labels), "other scripts never share a chunk"
        assert heard_as == expected_language(labels)
        start = end


@requires_node
def test_a_short_reply_is_spoken_as_one_chunk_and_a_language_change_splits_it():
    single = "Sure! I checked the logs and the deploy finished cleanly."
    mixed = (
        "Pronto, terminei o build e está tudo certo. The tests passed on every machine."
    )
    assert chunks_of([single, mixed], 200) == [
        [single],
        [
            "Pronto, terminei o build e está tudo certo. ",
            "The tests passed on every machine.",
        ],
    ]
