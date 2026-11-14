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


CHARACTER_REQUEST_SESSION = """
const { handleSetCharacterCommand } = require("./agent-commands/set-character-command-handler");
const { AvatarStateStore } = require("./avatar-session/avatar-state-store");
const sent = [];
const forwarded = [];
const avatarState = new AvatarStateStore();
const connection = { sendJson: (value) => sent.push(value) };
const rendererConnected = { value: true };
const context = {
  avatarState,
  textToSpeechGenerator: generator,
  clientRegistry: {
    sendToRenderer: (value) => {
      forwarded.push(value);
      return rendererConnected.value;
    },
  },
};
const request = (name, id) =>
  handleSetCharacterCommand({ name, id }, connection, context);
const spokenVoice = () => {
  generator.generate("oi", "turn", null, "neutral");
  return calls[calls.length - 1][2];
};
"""


@requires_node
def test_the_voice_follows_the_request_before_the_renderer_has_loaded():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        request("second", "request-1");
        const result = { voice: spokenVoice(), forwarded: forwarded.length };
        """
    )
    assert result == {"voice": "secondCloud", "forwarded": 1}


@requires_node
def test_asking_for_the_character_already_shown_answers_without_reloading():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        avatarState.applyCharacter("second");
        request("second", "request-2");
        const result = { voice: spokenVoice(), forwarded: forwarded.length, sent };
        """
    )
    assert result["forwarded"] == 0
    assert result["voice"] == "secondCloud"
    assert [
        (reply["type"], reply["name"], reply["id"]) for reply in result["sent"]
    ] == [("characterChanged", "second", "request-2")]


@requires_node
def test_asking_for_a_character_not_yet_shown_still_reaches_the_renderer():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        avatarState.applyCharacter("first");
        request("second", "request-3");
        const result = { forwarded, replies: sent.map((reply) => reply.type) };
        """
    )
    assert result["forwarded"] == [
        {"type": "setCharacter", "name": "second", "id": "request-3"}
    ]
    assert result["replies"] == ["characterRequested"]


@requires_node
def test_without_a_renderer_the_voice_stays_with_the_character_on_screen():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        rendererConnected.value = false;
        request("second", "request-4");
        const result = { voice: spokenVoice(), replies: sent.map((reply) => reply.type) };
        """
    )
    assert result == {"voice": "firstCloud", "replies": ["error"]}


@requires_node
def test_an_unknown_character_request_leaves_the_voice_alone():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        request("nobody", "request-5");
        const result = { voice: spokenVoice(), forwarded: forwarded.length };
        """
    )
    assert result == {"voice": "firstCloud", "forwarded": 1}
