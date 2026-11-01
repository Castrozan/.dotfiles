import shutil

import pytest

from renderer_module_runner import run_renderer_module

requires_node = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)

@requires_node
def test_unknown_pose_and_gesture_names_are_refused():
    result = run_renderer_module(
        "body-performance.js",
        """
        const body = new rendererModule.BodyPerformance(() => null);
        const refusal = (attempt) => { try { attempt(); } catch (error) { return error.message; } };
        console.log(JSON.stringify({
          pose: refusal(() => body.setPose("constructor")),
          gesture: refusal(() => body.playGesture("fly", 0)),
        }));
        """,
    )
    assert result == {
        "pose": "Unknown pose: constructor",
        "gesture": "Unknown gesture: fly",
    }


@requires_node
def test_a_gesture_moves_its_bones_and_then_returns_to_the_pose():
    result = run_renderer_module(
        "body-performance.js",
        """
        const bones = {};
        const body = new rendererModule.BodyPerformance((name) => (bones[name] ??= {
          rotation: { set(...angle) { this.angle = angle; } },
        }));
        const frame = (timestamp) => {
          body.update(timestamp, 0.066, {
            idleMode: "still", mouth: 0, headTurn: { yaw: 0, pitch: 0 },
          });
          return bones.head.rotation.angle[0];
        };
        body.playGesture("nod", 1000);
        const nodding = frame(1275);
        const finished = frame(2500);
        console.log(JSON.stringify({ nodding, finished }));
        """,
    )
    assert result["nodding"] < -0.15
    assert result["finished"] == pytest.approx(0)


@requires_node
def test_the_still_idle_mode_adds_no_motion():
    result = run_renderer_module(
        "body-performance.js",
        """
        const bones = {};
        const body = new rendererModule.BodyPerformance((name) => (bones[name] ??= {
          rotation: { set(...angle) { this.angle = angle; } },
        }));
        body.update(5000, 0.066, { idleMode: "still", mouth: 0, headTurn: { yaw: 0, pitch: 0 } });
        console.log(JSON.stringify(bones.head.rotation.angle));
        """,
    )
    assert result == [0, 0, 0]


@requires_node
def test_gaze_moves_toward_its_target_and_turns_the_head_with_it():
    result = run_renderer_module(
        "gaze.js",
        """
        const target = { position: { set(x, y, z) { this.value = [x, y, z]; } } };
        const gaze = new rendererModule.Gaze(target, { x: 0, y: 1, z: 2 });
        gaze.look("right");
        for (let index = 0; index < 60; index++) gaze.update(index * 66, 0.066, () => 0.5);
        const refused = (() => { try { gaze.look("toString"); } catch (error) { return error.message; } })();
        console.log(JSON.stringify({ position: target.position.value, head: gaze.headTurn(), refused }));
        """,
    )
    assert result["position"] == pytest.approx([0.8, 1, 2], abs=0.01)
    assert result["head"]["yaw"] > 0.3
    assert result["refused"] == "Unknown gaze target: toString"
