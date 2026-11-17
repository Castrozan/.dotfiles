import pytest
from control_server_node_runner import evaluate_node_json, requires_node


@requires_node
def test_the_acknowledgement_names_the_voice_source_that_spoke():
    result = evaluate_node_json(
        """
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const sent = [];
        const context = {
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "kokoro" }) },
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform(() => true)).finished;
              return { status: "finished" };
            },
          },
        };
        const connection = { sendJson: (message) => sent.push(message) };
        const result = handleSpeakCommand({ text: "oi", output: "none", id: "turn" }, connection, context)
          .then(() => sent);
        """
    )
    assert result == [
        {
            "type": "speakAck",
            "id": "turn",
            "output": "none",
            "status": "finished",
            "source": "kokoro",
        }
    ]


@requires_node
@pytest.mark.parametrize(
    ("output", "sinks"),
    [("speakers", ["AvatarLipSync", "default"]), ("remote", ["AvatarLipSync"])],
)
def test_every_output_drives_the_lip_sync_sink_and_only_speakers_reach_the_room(
    output, sinks
):
    result = evaluate_node_json(
        """
        const childProcess = require("child_process");
        const played = [];
        childProcess.spawn = (_, playerArguments) => {
          played.push(playerArguments[playerArguments.indexOf("--device") + 1]);
          return {
            stderr: { on: () => {} },
            on: (event, resolve) => event === "close" && resolve(),
            kill: () => {},
          };
        };
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const context = {
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "local" }) },
          speakerSinkName: "default",
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform(() => true)).finished;
              return { status: "finished" };
            },
          },
        };
        const result = handleSpeakCommand(
          { text: "oi", output: "OUTPUT", id: "turn" },
          { sendJson: () => {} },
          context,
        ).then(() => played);
        """.replace("OUTPUT", output)
    )
    assert result == sinks


@requires_node
def test_a_machine_with_its_own_player_speaks_through_it_and_not_the_sinks():
    result = evaluate_node_json(
        """
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const played = [];
        const context = {
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          textToSpeechGenerator: { generate: async () => ({ audioPath: "/a.wav", source: "local" }) },
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform(() => true)).finished;
              return { status: "finished" };
            },
          },
          playSpeech: (audioPath, output) => {
            played.push([audioPath, output]);
            return { finished: Promise.resolve(), stop: () => {} };
          },
        };
        const connection = { sendJson: () => {} };
        const result = handleSpeakCommand({ text: "oi", output: "speakers", id: "turn" }, connection, context)
          .then(() => played);
        """
    )
    assert result == [["/a.wav", "speakers"]]


@requires_node
def test_the_mac_player_reports_the_loudness_of_what_is_being_heard():
    result = evaluate_node_json(
        """
        const { levelAt, recordingOf } = require("./audio-playback/mac-seat-player");
        const rate = 24000;
        const header = Buffer.alloc(44);
        header.write("RIFF", 0);
        header.writeUInt32LE(rate, 24);
        header.write("data", 36);
        const samples = Buffer.alloc(rate * 2);
        for (let index = rate / 2; index < rate; index++) samples.writeInt16LE(16384, index * 2);
        const recording = recordingOf(Buffer.concat([header, samples]));
        const result = [-0.1, 0.1, 0.6, 2].map((seconds) => levelAt(recording, seconds));
        """
    )
    assert result == [0, 0, 0.5, 0]


@requires_node
def test_the_mac_player_silences_the_mouth_when_playback_ends_and_stops_on_demand():
    result = evaluate_node_json(
        """
        const childProcess = require("node:child_process");
        const fileSystem = require("node:fs");
        const signals = [];
        let ended;
        childProcess.spawn = (command, playerArguments) => ({
          stderr: { on: () => {} },
          on: (event, resolve) => { if (event === "close") ended = resolve; },
          kill: (signal) => { signals.push([command, playerArguments[0], signal]); ended(); },
        });
        const header = Buffer.alloc(44);
        header.writeUInt32LE(24000, 24);
        header.write("data", 36);
        const { playThroughTheMacSeat } = require("./audio-playback/mac-seat-player");
        fileSystem.readFileSync = () => Buffer.concat([header, Buffer.alloc(480)]);
        const levels = [];
        const playback = playThroughTheMacSeat((level) => levels.push(level))("/a.wav");
        playback.stop();
        const result = playback.finished.then(() => ({ signals, last: levels.at(-1) }));
        """
    )
    assert result == {
        "signals": [["avatar-seat-play", "/a.wav", "SIGTERM"]],
        "last": 0,
    }
