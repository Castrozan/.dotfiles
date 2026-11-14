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
