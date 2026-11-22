import json

import pytest
from control_server_node_runner import (
    CONTROL_SERVER_DIRECTORY,
    evaluate_node_json,
    requires_node,
)
from hypothesis import given, settings
from hypothesis import strategies as st

FUNCTION_WORDS = json.loads(
    (CONTROL_SERVER_DIRECTORY / "speech" / "language-function-words.json").read_text()
)
PORTUGUESE_SENTENCE = "Eu gosto muito de dançar no domingo à tarde."
ENGLISH_SENTENCE = (
    "The meeting went well, and the team agreed to ship the update on Friday."
)
JAPANESE_SENTENCE = "今日はとても天気がいいので、一緒に公園へ散歩に行きましょう。"
CHAIN = """
const { ResilientSpeechGenerator } = require("./speech/resilient-speech-generator");
const calls = [];
const record = (name, outcome) => async (...request) => {
  calls.push([name, ...request]);
  if (outcome instanceof Error) throw outcome;
  return { source: name };
};
const voices = {
  "pt-br": { kokoro: "pf_dora", piper: "faber" },
  "en-us": { kokoro: "af_heart", piper: "lessac" },
};
const chain = ({ cloud, kokoro = null, piper = null }) =>
  new ResilientSpeechGenerator(
    { generate: record("cloud", cloud) },
    { generate: record("kokoro", kokoro) },
    { generate: record("piper", piper) },
    "pt-br",
    voices,
  );
const offline = new Error("offline");
"""


def run_chain(script):
    return evaluate_node_json(CHAIN + script)


def detected_languages(sentences, home_language="pt-br"):
    return evaluate_node_json(
        f"""
        const {{ spokenLanguageOf }} = require("./speech/spoken-language");
        const result = {json.dumps(sentences)}.map(
          (sentence) => spokenLanguageOf(sentence, {json.dumps(home_language)}),
        );
        """
    )


@requires_node
def test_each_sentence_is_assigned_the_language_it_is_written_in():
    assert detected_languages(
        [PORTUGUESE_SENTENCE, ENGLISH_SENTENCE, JAPANESE_SENTENCE]
    ) == ["pt-br", "en-us", None]


@requires_node
@pytest.mark.parametrize("home_language", ["pt-br", "en-us"])
def test_a_sentence_without_evidence_keeps_the_home_language(home_language):
    assert (
        detected_languages(["Okay!", "...", ""], home_language) == [home_language] * 3
    )


def test_no_function_word_is_evidence_for_two_languages():
    assert not set(FUNCTION_WORDS["pt-br"]) & set(FUNCTION_WORDS["en-us"])


def sentences_of(language):
    return st.lists(
        st.lists(st.sampled_from(FUNCTION_WORDS[language]), min_size=1, max_size=8).map(
            " ".join
        ),
        min_size=1,
        max_size=4,
    )


@requires_node
@settings(max_examples=8, deadline=None)
@given(sentences=sentences_of("pt-br"))
def test_any_sentence_of_portuguese_function_words_is_portuguese(sentences):
    assert set(detected_languages(sentences, "en-us")) == {"pt-br"}


@requires_node
@settings(max_examples=8, deadline=None)
@given(sentences=sentences_of("en-us"))
def test_any_sentence_of_english_function_words_is_english(sentences):
    assert set(detected_languages(sentences, "pt-br")) == {"en-us"}


@requires_node
def test_the_cloud_is_told_the_language_of_each_sentence():
    result = run_chain(
        f"""
        const generator = chain({{ cloud: null }});
        const result = (async () => {{
          for (const text of {json.dumps([PORTUGUESE_SENTENCE, ENGLISH_SENTENCE, JAPANESE_SENTENCE])})
            await generator.generate(text, "turn", "voice", "happy");
          return calls.map((call) => call[call.length - 1]);
        }})();
        """
    )
    assert result == ["pt-br", "en-us", "en-us"]


@requires_node
def test_an_english_sentence_never_falls_back_to_a_portuguese_voice():
    result = run_chain(
        f"""
        const result = chain({{ cloud: offline }})
          .generate({json.dumps(ENGLISH_SENTENCE)}, "turn", "voice", "happy", {{ localVoice: "pm_alex" }})
          .then((speech) => ({{ source: speech.source, calls: calls.slice(1) }}));
        """
    )
    assert result == {
        "source": "kokoro",
        "calls": [["kokoro", ENGLISH_SENTENCE, "af_heart", "en-us"]],
    }


@requires_node
def test_an_english_sentence_reaches_the_english_piper_voice_when_kokoro_fails():
    result = run_chain(
        f"""
        const result = chain({{ cloud: offline, kokoro: offline }})
          .generate({json.dumps(ENGLISH_SENTENCE)}, "turn", "voice", "happy")
          .then((speech) => ({{ source: speech.source, piper: calls.at(-1) }}));
        """
    )
    assert result == {
        "source": "piper",
        "piper": ["piper", ENGLISH_SENTENCE, "turn", "lessac"],
    }


@requires_node
def test_a_portuguese_sentence_falls_back_to_the_character_brazilian_voice():
    result = run_chain(
        f"""
        const result = chain({{ cloud: offline }})
          .generate({json.dumps(PORTUGUESE_SENTENCE)}, "turn", "voice", "happy", {{ localVoice: "pm_alex" }})
          .then(() => calls.slice(1));
        """
    )
    assert result == [["kokoro", PORTUGUESE_SENTENCE, "pm_alex", "pt-br"]]


@requires_node
def test_a_sentence_no_local_voice_speaks_reports_the_cloud_failure():
    result = run_chain(
        f"""
        const result = chain({{ cloud: offline }})
          .generate({json.dumps(JAPANESE_SENTENCE)}, "turn", "voice", "happy")
          .then(() => "spoken", (error) => ({{ message: error.message, calls: calls.length }}));
        """
    )
    assert result == {"message": "offline", "calls": 1}
