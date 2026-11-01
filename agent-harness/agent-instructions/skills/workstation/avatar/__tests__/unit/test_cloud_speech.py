from control_server_node_runner import evaluate_node_json, requires_node

GENERATORS = """
const { ResilientSpeechGenerator } = require("./speech/resilient-speech-generator");
const calls = [];
const local = { generate: async (...request) => { calls.push(["local", ...request]); return { audioPath: "local" }; } };
"""


@requires_node
def test_cloud_failure_falls_back_to_the_local_default_voice():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async () => { throw new Error("offline"); } };
        const result = new ResilientSpeechGenerator(cloud, local)
          .generate("hello", "turn", "cloudVoice", "happy")
          .then((speech) => ({ audioPath: speech.audioPath, calls }));
        """
    )
    assert result["audioPath"] == "local"
    assert result["calls"] == [["local", "hello", "turn"]]


@requires_node
def test_a_local_voice_never_reaches_the_cloud():
    result = evaluate_node_json(
        GENERATORS
        + """
        const cloud = { generate: async () => { calls.push(["cloud"]); return {}; } };
        const result = new ResilientSpeechGenerator(cloud, local)
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
        const result = new ResilientSpeechGenerator(cloud, local)
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


@requires_node
def test_the_speech_result_is_read_after_the_operation_line():
    result = evaluate_node_json(
        """
        const { parseSpeechResult } = require("./speech/elevenlabs-speech-generator");
        const result = Promise.resolve(parseSpeechResult('{"operation_id": "a"}\\n{\\n "status": "succeeded"\\n}\\n'));
        """
    )
    assert result == {"status": "succeeded"}


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
