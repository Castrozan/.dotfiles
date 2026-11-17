import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "unit"))
from control_server_node_runner import evaluate_node_json, requires_node

SPEAK_ON_DISCORD = """
const childProcess = require("node:child_process");
const fileSystem = require("node:fs");
const spawned = [];
const signals = [];
let ended;
childProcess.spawn = (program, programArguments) => {
  spawned.push([program, ...programArguments]);
  return {
    stderr: { on: () => {} },
    on: (event, resolve) => { if (event === "close") ended = resolve; },
    kill: (signal) => { signals.push(signal); ended(); },
  };
};
const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
const { playThroughProgram } = require("./audio-playback/program-audio-player");
const header = Buffer.alloc(44);
header.writeUInt32LE(24000, 24);
header.write("data", 36);
fileSystem.readFileSync = () => Buffer.concat([header, Buffer.alloc(480)]);
const levels = [];
const announced = [];
const context = {
  clientRegistry: {
    hasRenderer: () => true,
    sendToRenderer: (message) => announced.push(message.type),
  },
  textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "local" }) },
  speakerSinkName: "default",
  playSpeech: playThroughProgram(["avatar-seat-play"], () => {}),
  playToDiscord: playThroughProgram(["discord-voice", "play"], (level) => levels.push(level)),
  speechFloor: {
    enqueue: async (_, perform) => {
      const playback = await perform(() => true);
      ENDS_PLAYBACK;
      await playback.finished;
      return { status: "finished" };
    },
  },
};
const result = handleSpeakCommand(
  { text: "oi", output: "discord", id: "turn" },
  { sendJson: () => {} },
  context,
).then(() => ({ spawned, signals, announced, last: levels.at(-1) }));
"""


def speak_on_discord(ends_playback):
    return evaluate_node_json(SPEAK_ON_DISCORD.replace("ENDS_PLAYBACK", ends_playback))


@requires_node
def test_discord_output_plays_only_through_the_discord_bridge():
    assert speak_on_discord("ended()") == {
        "spawned": [["discord-voice", "play", "/a.wav"]],
        "signals": [],
        "announced": ["startSpeaking", "speechEnded"],
        "last": 0,
    }


@requires_node
def test_stopping_discord_speech_sends_sigterm_to_the_bridge_player():
    assert speak_on_discord("playback.stop()") == {
        "spawned": [["discord-voice", "play", "/a.wav"]],
        "signals": ["SIGTERM"],
        "announced": ["startSpeaking", "speechEnded"],
        "last": 0,
    }
