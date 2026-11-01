from control_server_node_runner import evaluate_node_json, requires_node


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
