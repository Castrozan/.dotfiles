from control_server_node_runner import evaluate_node_json, requires_node

CHARACTER_VOICED_GENERATOR = """
const { CharacterVoicedSpeechGenerator } = require("./speech/character-voiced-speech-generator");
const calls = [];
const generator = new CharacterVoicedSpeechGenerator(
  { generate: (...call) => { calls.push(call); return "spoken"; } },
  [
    { name: "first", cloudVoice: "firstCloud", localVoice: "pf_first" },
    { name: "second", cloudVoice: "secondCloud", localVoice: "pm_second" },
  ],
);
"""


@requires_node
def test_speech_uses_the_first_character_until_another_is_selected():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + """
        generator.generate("oi", "turn-1", null, "happy");
        generator.selectCharacter("second");
        generator.generate("oi", "turn-2", null, "sad");
        const result = calls;
        """
    )
    assert result == [
        ["oi", "turn-1", "firstCloud", "happy", "pf_first"],
        ["oi", "turn-2", "secondCloud", "sad", "pm_second"],
    ]


@requires_node
def test_an_explicit_voice_outranks_the_character():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + """
        generator.generate("oi", "turn", "pf_dora", "neutral");
        const result = calls[0][2];
        """
    )
    assert result == "pf_dora"


@requires_node
def test_an_unknown_character_keeps_the_selected_voice():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + """
        generator.selectCharacter("second");
        generator.selectCharacter("nobody");
        generator.generate("oi", "turn", null, "neutral");
        const result = calls[0][2];
        """
    )
    assert result == "secondCloud"


@requires_node
def test_the_cloud_fallback_keeps_the_character_local_voice():
    result = evaluate_node_json(
        """
        const { ResilientSpeechGenerator } = require("./speech/resilient-speech-generator");
        const voices = [];
        const generator = new ResilientSpeechGenerator(
          { generate: async () => { throw new Error("offline"); } },
          { generate: async (text, voice) => { voices.push(voice); return { source: "kokoro" }; } },
          { generate: async () => ({ source: "piper" }) },
        );
        const result = generator
          .generate("oi", "turn", "cloudVoice", "neutral", "pm_alex")
          .then((speech) => ({ source: speech.source, voices }));
        """
    )
    assert result == {"source": "kokoro", "voices": ["pm_alex"]}
