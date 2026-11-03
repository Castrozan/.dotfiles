import json
import shutil
import subprocess
from pathlib import Path

import pytest

from renderer_module_runner import run_renderer_module


SOURCE = Path(__file__).resolve().parents[2] / "renderer/renderer-controls.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_renderer_controls_preserve_audio_state_consent_and_request_identity():
    program = r"""
    const fs = require("node:fs");
    class Channel { constructor() { this.sent = []; } postMessage(value) { this.sent.push(value); } }
    class Socket { constructor() { this.sent = []; } send(value) { this.sent.push(JSON.parse(value)); } }
    globalThis.BroadcastChannel = Channel;
    globalThis.WebSocket = Socket;
    globalThis.window = { avatarStatus: { levelMessages: 0 } };
    (async () => {
      const source = fs.readFileSync(process.argv[1], "utf8");
      const { RendererControls } = await import("data:text/javascript," + encodeURIComponent(source));
      const state = { mouth: 0, mode: "avatar" };
      let active = false;
      let chosen;
      const controls = new RendererControls(state, {
        setExpression: value => { state.expression = value.expression; },
        showMode: async mode => { if (mode !== "avatar" && !active) throw new Error("Enable camera first"); state.mode = mode; },
        enableCamera: async identifier => { active = true; chosen = identifier; },
        disableCamera: () => { active = false; state.mode = "avatar"; },
        cameraActive: () => active,
        currentCharacter: () => "vita",
      });
      controls.connect(); controls.socket.onopen();
      controls.dispatch({ type: "audioLevel", level: 0.1 });
      controls.dispatch({ type: "setIdle", mode: "floating" });
      controls.dispatch({ type: "updateExpression", expression: "happy" });
      controls.dispatch({ type: "constructor" });
      await controls.handleLocal({ data: { type: "enableCamera", deviceId: "chosen" } });
      await controls.requestVideoMode({ mode: "composite", id: "allowed" });
      await controls.handleLocal({ data: { type: "disableCamera" } });
      await controls.requestVideoMode({ mode: "camera", id: "denied" });
      console.log(JSON.stringify({ state, chosen, levels: window.avatarStatus.levelMessages, socket: controls.socket.sent, local: controls.channel.sent }));
    })().catch(error => { console.error(error); process.exitCode = 1; });
    """
    completed = subprocess.run(
        ["node", "-e", program, str(SOURCE)], capture_output=True, text=True, check=True
    )
    result = json.loads(completed.stdout)
    assert result["state"]["mouthTarget"] == pytest.approx(0.8)
    assert result["state"]["idleMode"] == "floating"
    assert result["state"]["expression"] == "happy"
    assert result["state"]["mode"] == "avatar"
    assert result["chosen"] == "chosen"
    assert result["levels"] == 1
    assert result["socket"][-2] == {
        "type": "videoModeChanged",
        "mode": "composite",
        "id": "allowed",
    }
    assert result["socket"][-1] == {
        "type": "videoModeError",
        "message": "Enable camera first",
        "id": "denied",
    }
    assert result["local"][-1]["message"] == "Camera released"


def follow_level(current, target, delta):
    program = f"""
    const fs = require("node:fs");
    globalThis.BroadcastChannel = class {{}};
    (async () => {{
      const source = fs.readFileSync(process.argv[1], "utf8");
      const {{ followLevel }} = await import("data:text/javascript," + encodeURIComponent(source));
      console.log(followLevel({current}, {target}, {delta}));
    }})();
    """
    completed = subprocess.run(
        ["node", "-e", program, str(SOURCE)], capture_output=True, text=True, check=True
    )
    return float(completed.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_mouth_opens_quickly_but_settles_without_flapping():
    opening = follow_level(0, 1, 0.033)
    closing = 1 - follow_level(1, 0, 0.033)
    assert 0 < closing < opening < 1


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_mouth_following_is_stable_on_a_long_frame():
    assert follow_level(0, 1, 10) == pytest.approx(1)


def test_the_output_page_keeps_its_canvas_away_until_it_is_presented():
    renderer = (SOURCE.parent / "renderer.js").read_text()
    assert "setPresented(false);" in renderer
    assert 'output.style.display = presented ? "" : "none";' in renderer


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_a_presence_message_reaches_the_renderer():
    result = run_renderer_module(
        "renderer-controls.js",
        """
        globalThis.window = { avatarStatus: {} };
        globalThis.BroadcastChannel = class {};
        const presented = [];
        const controls = new rendererModule.RendererControls(
          {},
          { setPresented: (value) => presented.push(value) },
        );
        controls.dispatch({ type: "setPresented", presented: true });
        controls.dispatch({ type: "setPresented", presented: false });
        console.log(JSON.stringify(presented));
        """,
    )
    assert result == [True, False]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_she_replaces_the_camera_only_while_she_speaks():
    result = run_renderer_module(
        "renderer-controls.js",
        """
        globalThis.window = { avatarStatus: {} };
        globalThis.BroadcastChannel = class {};
        const state = {};
        const controls = new rendererModule.RendererControls(state, {
          beginSpeech: () => {},
          endSpeech: () => {},
        });
        const seen = () => rendererModule.visibleMode("camera", state.speaking);
        const before = seen();
        controls.dispatch({ type: "startSpeaking" });
        const during = seen();
        const composite = rendererModule.visibleMode("composite", state.speaking);
        controls.dispatch({ type: "speechEnded" });
        console.log(JSON.stringify({ before, during, composite, after: seen() }));
        """,
    )
    assert result == {
        "before": "camera",
        "during": "avatar",
        "composite": "composite",
        "after": "camera",
    }


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_the_emotion_mouth_stays_away_between_syllables_and_returns_after_speech():
    result = run_renderer_module(
        "renderer-controls.js",
        """
        console.log(JSON.stringify({
          betweenSyllables: rendererModule.emotionMouthTarget(1300, 1000),
          afterSpeech: rendererModule.emotionMouthTarget(1500, 1000),
          beforeAnySpeech: rendererModule.emotionMouthTarget(0, -Infinity),
        }));
        """,
    )
    assert result == {"betweenSyllables": 0, "afterSpeech": 1, "beforeAnySpeech": 1}


def voice_openings(levels):
    return run_renderer_module(
        "renderer-controls.js",
        f"""
        let peak = 0;
        const openings = {levels}.map((level) => {{
          peak = rendererModule.followVoicePeak(peak, level);
          return rendererModule.mouthOpening(level, peak);
        }});
        console.log(JSON.stringify(openings));
        """,
    )


def test_a_quiet_voice_opens_the_mouth_as_far_as_a_loud_one():
    quiet = voice_openings([0.1, 0.05, 0.1])
    loud = voice_openings([0.3, 0.15, 0.3])
    assert quiet == pytest.approx(loud)
    assert max(quiet) == pytest.approx(0.8)


def test_the_mouth_closes_between_syllables():
    syllable, gap = voice_openings([0.1, 0.0])
    assert syllable == pytest.approx(0.8)
    assert gap == 0


def test_faint_room_noise_barely_moves_the_mouth():
    assert voice_openings([0.005]) == pytest.approx([0.05])
