import json

from control_server_node_runner import evaluate_node_json, requires_node
from hypothesis import given, settings
from hypothesis import strategies as st

MAXIMUM_TEXT_CHARACTERS = 4000
OBSERVED_FIXED_SECONDS = 1.21 + 2.7
OBSERVED_SECONDS_PER_CHARACTER = 0.01451
HUNDRED_AND_SEVENTY_WORDS = 1000


def timeouts_for(lengths):
    return evaluate_node_json(
        f"""
        const timeouts = [];
        const clientPath = require.resolve("./speech/media-speech-client");
        require.cache[clientPath] = {{ exports: {{ runMediaSpeech: async (args, timeout) => {{
          timeouts.push(timeout);
          return {{ audio: {{ path: "/test.wav", duration_seconds: 1 }}, alignment: {{ status: "unavailable" }} }};
        }} }} }};
        const {{ ElevenLabsSpeechGenerator }} = require("./speech/elevenlabs-speech-generator");
        const generator = new ElevenLabsSpeechGenerator("voice", "pt-br");
        const result = (async () => {{
          for (const length of {json.dumps(lengths)})
            await generator.generate("a".repeat(length), null, "happy");
          return timeouts;
        }})();
        """
    )


@requires_node
@settings(max_examples=8, deadline=None)
@given(
    lengths=st.lists(
        st.integers(min_value=1, max_value=MAXIMUM_TEXT_CHARACTERS),
        min_size=1,
        max_size=6,
    )
)
def test_the_cloud_timeout_covers_the_measured_latency_of_every_text_length(lengths):
    timeouts = timeouts_for(lengths)
    for length, timeout in zip(lengths, timeouts, strict=True):
        measured_worst_milliseconds = (
            OBSERVED_FIXED_SECONDS + OBSERVED_SECONDS_PER_CHARACTER * length
        ) * 1000
        assert 15000 <= timeout <= 120000
        assert timeout >= measured_worst_milliseconds


@requires_node
def test_a_longer_text_never_gets_a_shorter_timeout():
    lengths = list(range(1, MAXIMUM_TEXT_CHARACTERS + 1, 97))
    timeouts = timeouts_for(lengths)
    assert timeouts == sorted(timeouts)


@requires_node
def test_a_long_reply_outlasts_the_former_fixed_fifteen_second_limit():
    [timeout] = timeouts_for([HUNDRED_AND_SEVENTY_WORDS])
    assert timeout > 15000
