import base64
import json
import shutil
import subprocess

import pytest
from page_devices import BUILT_IN_OUTPUT, CALL_MICROPHONE, CALL_SPEAKER, MEETING_SEAT

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


def join_meeting(devices, levels=None):
    source = base64.b64encode(MEETING_SEAT.read_bytes()).decode()
    program = f"""
    const log = [];
    const gains = [];
    const track = {{ stop: () => log.push("track stopped") }};
    const stream = (name) => ({{ name, getTracks: () => [track] }});
    class Context {{
      constructor(name) {{
        this.name = name;
        this.state = "running";
        this.destination = {{ name: "destination" }};
      }}
      setSinkId(id) {{ log.push(["sink", id]); }}
      createMediaStreamSource(source) {{
        return {{
          connect: (node) => {{
            log.push(["source", this.name, source.name]);
            node.fedBy = source.name;
          }},
        }};
      }}
      createGain() {{
        const node = {{
          gain: {{ value: 1 }},
          connect: (target) => {{ node.reaches = target.name; }},
        }};
        gains.push(node);
        return node;
      }}
      createMediaStreamDestination() {{ return {{ stream: stream("voice for the call") }}; }}
      resume() {{}}
      close() {{ this.state = "closed"; log.push(["closed", this.name]); }}
    }}
    globalThis.AudioContext = class extends Context {{ constructor() {{ super("call microphone"); }} }};
    globalThis.AudioWorkletNode = class {{
      constructor(context, name, options) {{
        log.push(["worklet", name, options]);
        this.port = {{}};
      }}
    }};
    globalThis.Audio = class {{ play() {{ log.push("earpiece plays"); }} }};
    globalThis.location = {{ host: "localhost:8769" }};
    globalThis.WebSocket = class {{
      static OPEN = 1;
      constructor(url) {{
        log.push(["socket", url]);
        setTimeout(() => this.onopen(), 0);
      }}
      close() {{ log.push("socket closed"); }}
    }};
    Object.defineProperty(globalThis, "navigator", {{ configurable: true, value: {{ mediaDevices: {{
      enumerateDevices: async () => {json.dumps(devices)},
      getUserMedia: async (constraints) => {{
        log.push(["capture", constraints.audio]);
        return stream("call audio");
      }},
    }} }} }});
    import("data:text/javascript;base64,{source}").then(async (meeting) => {{
      const voiceConnections = [];
      try {{
        const joined = await meeting.joinMeeting({{
          microphone: stream("microphone"),
          playback: new Context("playback"),
          voice: {{ connect: (destination) => voiceConnections.push(destination.stream.name) }},
          openAudioGraph: async (rate) => new Context(`capture ${{rate}}`),
        }});
        log.push("joined");
        const levels = {json.dumps(levels)};
        if (levels) joined.setLevels(levels);
        joined.leave();
      }} catch (error) {{
        log.push(["failed", error.message]);
      }}
      const routes = Object.fromEntries(gains.map((node) => [node.fedBy, node.reaches]));
      const gainValues = Object.fromEntries(gains.map((node) => [node.fedBy, node.gain.value]));
      console.log(JSON.stringify({{ log, voiceConnections, routes, gainValues }}));
    }});
    """
    completed = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(completed.stdout)


def test_joining_routes_the_call_and_the_voice_through_the_virtual_devices():
    result = join_meeting([BUILT_IN_OUTPUT, CALL_MICROPHONE, CALL_SPEAKER])
    log = result["log"]
    capture = next(entry for entry in log if entry[0] == "capture")[1]
    assert capture == {
        "deviceId": {"exact": "in-16"},
        "echoCancellation": False,
        "noiseSuppression": False,
        "autoGainControl": False,
    }
    assert ["socket", "ws://localhost:8769/meeting"] in log
    assert [
        "worklet",
        "microphone-frames",
        {"channelCount": 1, "channelCountMode": "explicit"},
    ] in log
    assert ["sink", "out-2"] in log
    assert ["source", "call microphone", "microphone"] in log
    assert ["source", "call microphone", "voice for the call"] in log
    assert result["voiceConnections"] == ["voice for the call"]
    assert "earpiece plays" in log
    assert log.index("joined") < log.index("socket closed")
    assert ["closed", "capture 16000"] in log
    assert ["closed", "call microphone"] in log


def test_both_streams_reach_the_call_through_their_own_gain():
    result = join_meeting([BUILT_IN_OUTPUT, CALL_MICROPHONE, CALL_SPEAKER])
    assert result["routes"] == {
        "microphone": "destination",
        "voice for the call": "destination",
    }
    assert result["gainValues"] == {"microphone": 1, "voice for the call": 1}


def test_levels_set_the_named_channels_and_ignore_unknown_names():
    result = join_meeting(
        [BUILT_IN_OUTPUT, CALL_MICROPHONE, CALL_SPEAKER],
        levels={"human": 0, "agent": 0.5, "constructor": 1, "ghost": 0.1},
    )
    assert result["gainValues"] == {"microphone": 0, "voice for the call": 0.5}
    assert "joined" in result["log"]
    assert all(entry[0] != "failed" for entry in result["log"])


def test_a_missing_device_fails_before_any_capture_or_socket_opens():
    result = join_meeting([BUILT_IN_OUTPUT, CALL_MICROPHONE])
    assert len(result["log"]) == 1
    failure = result["log"][0]
    assert failure[0] == "failed"
    assert "missing: BlackHole 16ch" in failure[1]
