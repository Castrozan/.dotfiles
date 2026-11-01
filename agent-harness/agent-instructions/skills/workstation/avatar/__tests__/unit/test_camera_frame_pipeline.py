from control_server_node_runner import evaluate_node_json, requires_node

PIPELINE = """
const childProcess = require("child_process");
const spawned = [];
const written = [];
childProcess.spawn = (command, arguments_) => {
  spawned.push({ command, arguments_ });
  const events = { on: () => {} };
  return {
    ...events,
    stderr: events,
    stdin: { ...events, destroyed: false, writableNeedDrain: false, write: (frame) => written.push(frame) },
  };
};
const { VideoDeviceFramePipeline } = require("./virtual-camera/video-device-frame-pipeline");
const pipeline = new VideoDeviceFramePipeline({
  framesPerSecond: 60, width: 1280, height: 720, videoDevice: "/dev/video10",
});
"""


@requires_node
def test_raw_frames_are_flipped_upright_and_written_to_the_device():
    result = evaluate_node_json(
        PIPELINE
        + """
        const result = spawned[0].arguments_.join(" ");
        """
    )
    assert "-f rawvideo -pixel_format rgba -video_size 1280x720" in result
    assert "-framerate 60 -i pipe:0 -vf vflip" in result
    assert result.endswith("-f v4l2 /dev/video10")


@requires_node
def test_a_frame_is_skipped_while_the_encoder_is_still_draining():
    result = evaluate_node_json(
        PIPELINE
        + """
        const first = pipeline.writeFrame("frame");
        pipeline.encoder.stdin.writableNeedDrain = true;
        const second = pipeline.writeFrame("frame");
        const result = { first, second, written: written.length };
        """
    )
    assert result == {"first": True, "second": False, "written": 1}
