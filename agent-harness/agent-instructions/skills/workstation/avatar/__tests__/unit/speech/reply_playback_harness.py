REPLY_PLAYBACK_HARNESS = """
const childProcess = require("child_process");
const players = [];
childProcess.spawn = (_, playerArguments) => {
  const closers = [];
  const player = {
    sink: playerArguments[playerArguments.indexOf("--device") + 1],
    audio: playerArguments.at(-1),
    signals: [],
    stderr: { on: () => {} },
    on: (event, close) => event === "close" && closers.push(close),
    kill: (signal) => { player.signals.push(signal); player.finish(); },
    finish: () => closers.splice(0).forEach((close) => close()),
  };
  players.push(player);
  return player;
};
const { SpeechFloor } = require("./speech/speech-floor");
const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
const { handleStopSpeakingCommand } = require("./agent-commands/stop-speaking-command-handler");
const settle = () => new Promise((resolve) => setTimeout(resolve, 5));
const firstWord = (text) => text.trim().split(" ")[0];
const rendererMessages = [];
const agentMessages = [];
const synthesized = [];
let synthesize = async (text) => ({ audioPath: `/${firstWord(text)}.wav`, source: "elevenlabs" });
const context = {
  clientRegistry: {
    hasRenderer: () => true,
    sendToRenderer: (message) => rendererMessages.push(
      message.type === "startSpeaking" ? `start:${firstWord(message.text)}` : message.type,
    ),
  },
  speakerSinkName: "default",
  speechFloor: new SpeechFloor({ async open() { return async () => {}; } }),
  textToSpeechGenerator: {
    generate: (text, ...request) => {
      synthesized.push(firstWord(text));
      return synthesize(text, ...request);
    },
  },
};
const connection = { sendJson: (message) => agentMessages.push(message) };
const speak = (text, id = "turn") =>
  handleSpeakCommand({ text, output: "speakers", id }, connection, context);
const bargeIn = () => handleStopSpeakingCommand({}, connection, context);
const roomPlayers = () => players.filter((player) => player.sink === "default");
const finishRoomPlayback = async () => {
  await settle();
  players.forEach((player) => player.finish());
  await settle();
};
"""
