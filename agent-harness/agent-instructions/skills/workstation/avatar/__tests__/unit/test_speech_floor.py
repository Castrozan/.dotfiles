from control_server_node_runner import evaluate_node_json, requires_node

FLOOR_HARNESS = """
const { SpeechFloor } = require("./speech/speech-floor");
const events = [];
const channel = {
  async open() {
    events.push("open");
    return async () => events.push("close");
  },
};
const floor = new SpeechFloor(channel);
const turn = (name) => {
  let finish;
  const finished = new Promise((resolve) => { finish = resolve; });
  return {
    finish,
    perform: async () => {
      events.push(`speak:${name}`);
      return { finished, stop() { events.push(`stop:${name}`); finish(); } };
    },
  };
};
const settle = () => new Promise((resolve) => setTimeout(resolve, 5));
"""


@requires_node
def test_agents_speak_in_arrival_order_without_overlapping():
    result = evaluate_node_json(
        FLOOR_HARNESS
        + """
        const first = turn("first");
        const second = turn("second");
        const firstResult = floor.enqueue(true, first.perform);
        const secondResult = floor.enqueue(true, second.perform);
        const result = (async () => {
          await settle();
          const whileFirstSpeaks = [...events];
          first.finish();
          await firstResult;
          await settle();
          second.finish();
          await secondResult;
          return { whileFirstSpeaks, events };
        })();
        """
    )
    assert result["whileFirstSpeaks"] == ["open", "speak:first"]
    assert result["events"] == [
        "open",
        "speak:first",
        "close",
        "open",
        "speak:second",
        "close",
    ]


@requires_node
def test_interrupting_stops_the_speaker_and_drops_everyone_waiting():
    result = evaluate_node_json(
        FLOOR_HARNESS
        + """
        const first = turn("first");
        const second = turn("second");
        const firstResult = floor.enqueue(true, first.perform);
        const secondResult = floor.enqueue(true, second.perform);
        const result = (async () => {
          await settle();
          floor.interrupt();
          return {
            first: await firstResult,
            second: await secondResult,
            events,
          };
        })();
        """
    )
    assert result["first"]["status"] == "interrupted"
    assert result["second"]["status"] == "cancelled"
    assert result["events"] == ["open", "speak:first", "stop:first", "close"]


@requires_node
def test_speech_away_from_the_meeting_leaves_the_channel_closed():
    result = evaluate_node_json(
        FLOOR_HARNESS
        + """
        const room = turn("room");
        const spoken = floor.enqueue(false, room.perform);
        const result = (async () => {
          await settle();
          room.finish();
          await spoken;
          return events;
        })();
        """
    )
    assert result == ["speak:room"]


@requires_node
def test_a_failed_turn_closes_the_channel_and_keeps_the_floor_usable():
    result = evaluate_node_json(
        FLOOR_HARNESS
        + """
        const after = turn("after");
        const result = (async () => {
          const failure = await floor
            .enqueue(true, async () => { throw new Error("no voice"); })
            .catch((error) => error.message);
          const spoken = floor.enqueue(true, after.perform);
          await settle();
          after.finish();
          await spoken;
          return { failure, events };
        })();
        """
    )
    assert result["failure"] == "no voice"
    assert result["events"] == ["open", "close", "open", "speak:after", "close"]


@requires_node
def test_gate_restores_the_mute_state_the_turn_found():
    result = evaluate_node_json(
        """
        const Module = require("node:module");
        const original = Module._load;
        const calls = [];
        let agentMuted = true;
        Module._load = function(name, ...arguments_) {
          if (name === "node:child_process") return { execFile: (command, args, callback) => {
            calls.push(args.join(" "));
            callback(null, JSON.stringify({ running: true, channels: { agent: { mute: agentMuted } } }), "");
          } };
          return original.call(this, name, ...arguments_);
        };
        const { AgentChannelGate } = require("./speech/agent-channel-gate");
        const gate = new AgentChannelGate();
        const result = (async () => {
          const release = await gate.open();
          await release();
          const mutedCalls = [...calls];
          calls.length = 0;
          agentMuted = false;
          const keepOpen = await gate.open();
          await keepOpen();
          return { mutedCalls, openCalls: calls };
        })();
        """
    )
    assert result["mutedCalls"] == ["status", "mute agent 0", "mute agent 1"]
    assert result["openCalls"] == ["status"]


@requires_node
def test_gate_refuses_to_speak_without_the_owned_audio_graph():
    result = evaluate_node_json(
        """
        const Module = require("node:module");
        const original = Module._load;
        Module._load = function(name, ...arguments_) {
          if (name === "node:child_process") return { execFile: (command, args, callback) =>
            callback(null, JSON.stringify({ running: false, channels: {} }), "") };
          return original.call(this, name, ...arguments_);
        };
        const { AgentChannelGate } = require("./speech/agent-channel-gate");
        const result = new AgentChannelGate().open().catch((error) => error.message);
        """
    )
    assert result == "Avatar audio is not running; run avatar-start"


@requires_node
def test_camera_frames_come_from_the_canvas_not_the_compositor():
    result = evaluate_node_json(
        """
        const { readCanvasFrame } = require("./virtual-camera/canvas-frame-reader");
        const requests = [];
        const session = {
          sendAndAwaitResult: async (method, parameters) => {
            requests.push({ method, parameters });
            return { result: { value: Buffer.from("frame").toString("base64") } };
          },
        };
        const result = readCanvasFrame(session, 85).then((frame) => ({
          text: frame.toString(),
          method: requests[0].method,
          expression: requests[0].parameters.expression,
        }));
        """
    )
    assert result["text"] == "frame"
    assert result["method"] == "Runtime.evaluate"
    assert "avatarFrameJpeg" in result["expression"]
    assert "0.85" in result["expression"]


@requires_node
def test_no_frame_is_written_before_the_renderer_can_supply_one():
    result = evaluate_node_json(
        """
        const { readCanvasFrame } = require("./virtual-camera/canvas-frame-reader");
        const session = { sendAndAwaitResult: async () => ({ result: {} }) };
        const result = readCanvasFrame(session, 85).then((frame) => ({ frame }));
        """
    )
    assert result["frame"] is None
