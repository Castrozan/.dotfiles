import json
from itertools import accumulate

from control_server_node_runner import evaluate_node_json, requires_node
from hypothesis import assume, given, settings
from hypothesis import strategies as st

ANY_TEXT = st.text(st.characters(exclude_categories=["Cs"]), min_size=1, max_size=700)
WORDS = st.lists(
    st.text("abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12),
    min_size=1,
    max_size=8,
)
LONGEST_PHRASE = 8 * 12 + 7 + 2
EXAMPLES = settings(max_examples=40, deadline=None)

SENTENCES = st.lists(
    st.tuples(WORDS, st.sampled_from([". ", "! ", "? "])).map(
        lambda parts: " ".join(parts[0]).capitalize() + parts[1]
    ),
    min_size=1,
    max_size=12,
)
CLAUSES = st.lists(
    st.tuples(WORDS, st.sampled_from([", ", "; ", ": "])).map(
        lambda parts: " ".join(parts[0]) + parts[1]
    ),
    min_size=2,
    max_size=12,
)


def chunks_of(texts, maximum):
    return evaluate_node_json(
        f"""
        const {{ speechChunks }} = require("./speech/speech-chunks");
        const result = {json.dumps(texts)}.map((text) => speechChunks(text, {maximum}));
        """
    )


def spoken_length(text):
    return len(text.encode("utf-16-le")) // 2


def ends_of(pieces):
    return set(accumulate(map(len, pieces)))


@requires_node
@EXAMPLES
@given(
    texts=st.lists(ANY_TEXT, min_size=1, max_size=6),
    maximum=st.integers(min_value=2, max_value=240),
)
def test_any_text_splits_into_bounded_chunks_that_rebuild_it(texts, maximum):
    for text, chunks in zip(texts, chunks_of(texts, maximum), strict=True):
        assert "".join(chunks) == text
        assert all(0 < spoken_length(chunk) <= maximum for chunk in chunks)


@requires_node
@EXAMPLES
@given(
    sentences=SENTENCES,
    maximum=st.integers(min_value=LONGEST_PHRASE, max_value=240),
)
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
@given(clauses=CLAUSES, maximum=st.integers(min_value=LONGEST_PHRASE, max_value=200))
def test_a_sentence_too_long_to_fit_breaks_only_after_its_clauses(clauses, maximum):
    sentence = "".join(clauses).capitalize().rstrip(",;: ") + "."
    assume(len(sentence) > maximum)
    (chunks,) = chunks_of([sentence], maximum)
    assert ends_of(chunks[:-1]) <= ends_of(clauses[:-1])


@requires_node
def test_a_short_reply_is_spoken_as_one_chunk():
    reply = "Sure, I checked the logs and the deploy finished cleanly."
    assert chunks_of([reply], 200) == [[reply]]
