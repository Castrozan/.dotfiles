from control_server_node_runner import evaluate_node_json, requires_node

GENERATORS = """
const { ResilientSpeechGenerator } = require("./speech/resilient-speech-generator");
const calls = [];
const kokoro = { generate: async (...request) => { calls.push(["kokoro", ...request]); return { audioPath: "kokoro" }; } };
const local = { generate: async (...request) => { calls.push(["local", ...request]); return { audioPath: "local" }; } };
"""


@requires_node
def test_cloud_failure_falls_back_to_the_kokoro_default_voice():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async () => { throw new Error("offline"); } };
        const result = new ResilientSpeechGenerator(cloud, kokoro, local)
          .generate("hello", "turn", "cloudVoice", "happy")
          .then((speech) => ({ audioPath: speech.audioPath, calls }));
        """
    )
    assert result["audioPath"] == "kokoro"
    assert result["calls"] == [["kokoro", "hello"]]


@requires_node
def test_piper_speaks_only_when_cloud_and_kokoro_both_fail():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async () => { throw new Error("offline"); } };
        const failingKokoro = { generate: async () => { throw new Error("no model"); } };
        const result = new ResilientSpeechGenerator(cloud, failingKokoro, local)
          .generate("hello", "turn", "cloudVoice", "happy")
          .then((speech) => ({ audioPath: speech.audioPath, calls }));
        """
    )
    assert result["audioPath"] == "local"
    assert result["calls"] == [["local", "hello", "turn"]]


@requires_node
def test_a_kokoro_voice_never_reaches_the_cloud():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async () => { calls.push(["cloud"]); return {}; } };
        const result = new ResilientSpeechGenerator(cloud, kokoro, local)
          .generate("olá", "turn", "pf_dora", "sad")
          .then(() => calls);
        """
    )
    assert result == [["kokoro", "olá", "pf_dora"]]


@requires_node
def test_a_piper_voice_never_reaches_the_cloud():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async () => { calls.push(["cloud"]); return {}; } };
        const result = new ResilientSpeechGenerator(cloud, kokoro, local)
          .generate("olá", "turn", "pt_BR-faber-medium", "sad")
          .then(() => calls);
        """
    )
    assert result == [["local", "olá", "turn", "pt_BR-faber-medium"]]


@requires_node
def test_the_cloud_receives_the_voice_and_emotion():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async (...request) => { calls.push(request); return {}; } };
        const result = new ResilientSpeechGenerator(cloud, kokoro, local)
          .generate("hi", "turn", undefined, "happy")
          .then(() => calls);
        """
    )
    assert result == [["hi", None, "happy"]]


@requires_node
def test_spoken_vowels_skip_the_delivery_tag_and_read_accents():
    result = evaluate_node_json(
        """
        const { spokenVowels } = require("./speech/spoken-vowels");
        const characters = [..."[warm] Só"];
        const result = Promise.resolve(spokenVowels({
          characters,
          starts_seconds: characters.map((_, index) => index),
          ends_seconds: characters.map((_, index) => index + 1),
        }));
        """
    )
    assert result == [{"shape": "oh", "start": 8, "end": 9}]


def fake_media_speech(directory):
    executable = directory / "media-speech"
    executable.write_text(
        """#!/bin/sh
echo '{"operation_id": "a"}' >&2
printf '{\\n  "status": "succeeded",\\n  "audio": {"path": "/speech.wav", "duration_seconds": 1.5},\\n  "alignment": {"status": "unavailable"}\\n}\\n'
"""
    )
    executable.chmod(0o755)
    return f'process.env.PATH = "{directory}:" + process.env.PATH;'


@requires_node
def test_elevenlabs_reads_the_pretty_printed_media_speech_result(tmp_path):
    result = evaluate_node_json(
        fake_media_speech(tmp_path)
        + """
        const { ElevenLabsSpeechGenerator } = require("./speech/elevenlabs-speech-generator");
        const result = new ElevenLabsSpeechGenerator("voice", "pt-br").generate("oi", null, "happy");
        """
    )
    assert result == {
        "audioPath": "/speech.wav",
        "duration": 1.5,
        "vowels": [],
        "source": "elevenlabs",
    }


@requires_node
def test_kokoro_reads_the_pretty_printed_media_speech_result(tmp_path):
    result = evaluate_node_json(
        fake_media_speech(tmp_path)
        + """
        const { KokoroSpeechGenerator } = require("./speech/kokoro-speech-generator");
        const result = new KokoroSpeechGenerator("pf_dora", "pt-br").generate("oi");
        """
    )
    assert result == {
        "audioPath": "/speech.wav",
        "duration": 1.5,
        "vowels": [],
        "source": "kokoro",
    }


@requires_node
def test_performing_without_a_renderer_is_an_error():
    result = evaluate_node_json(
        """
        const { handlePerformCommand } = require("./agent-commands/perform-command-handler");
        const sent = [];
        const connection = { sendJson: (message) => sent.push(message), send: (message) => sent.push(JSON.parse(message)) };
        handlePerformCommand(
          { action: "gesture", name: "wave", id: "a" },
          connection,
          { clientRegistry: { sendToRenderer: () => false } },
        );
        const result = Promise.resolve(sent);
        """
    )
    assert result[0]["type"] == "error"
