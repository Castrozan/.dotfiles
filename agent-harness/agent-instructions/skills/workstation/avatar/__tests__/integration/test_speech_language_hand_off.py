import json
import tempfile
from pathlib import Path

import pytest
from control_server_node_runner import evaluate_node_json, requires_node
from hypothesis import example, given, settings
from hypothesis import strategies as st

RECORDING_MEDIA_SPEECH = """#!/bin/sh
while [ $# -gt 0 ]; do
  [ "$1" = "--language" ] && printf '%s\\n' "$2" >> "$(dirname "$0")/languages"
  shift
done
printf '{"audio": {"path": "/speech.wav", "duration_seconds": 1}, "alignment": {"status": "unavailable"}}'
"""
GENERATORS = [
    ("ElevenLabsSpeechGenerator", "elevenlabs-speech-generator", '"oi", null, "happy"'),
    ("KokoroSpeechGenerator", "kokoro-speech-generator", '"oi", null'),
]
LANGUAGE_TAGS = st.lists(
    st.from_regex(r"[a-z]{2}-[a-z]{2}", fullmatch=True), min_size=1, max_size=3
)


def languages_sent_to_media_speech(directory, generator, module, arguments, languages):
    executable = directory / "media-speech"
    executable.write_text(RECORDING_MEDIA_SPEECH)
    executable.chmod(0o755)
    evaluate_node_json(
        f"""
        process.env.PATH = "{directory}:" + process.env.PATH;
        const {{ {generator} }} = require("./speech/{module}");
        const result = (async () => {{
          for (const language of {json.dumps(languages)})
            await new {generator}("voice", language).generate({arguments});
          return true;
        }})();
        """
    )
    return (directory / "languages").read_text().splitlines()


@requires_node
@pytest.mark.parametrize("generator,module,arguments", GENERATORS)
@settings(max_examples=6, deadline=None)
@example(languages=["pt-br"])
@given(languages=LANGUAGE_TAGS)
def test_the_configured_language_reaches_media_speech_with_its_region(
    generator, module, arguments, languages
):
    with tempfile.TemporaryDirectory() as directory:
        assert (
            languages_sent_to_media_speech(
                Path(directory), generator, module, arguments, languages
            )
            == languages
        )
