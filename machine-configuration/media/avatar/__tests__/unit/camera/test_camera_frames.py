from renderer_module_runner import run_renderer_module


def clock_run(draw):
    return f"""
    let now = 0;
    const delays = [];
    const pending = [];
    const clock = {{
      performance: {{ now: () => now }},
      setTimeout: (callback, delay) => {{ delays.push(delay); pending.push(callback); }},
    }};
    let draws = 0;
    {draw}
    rendererModule.startFrameClock(60, drawFrame, clock);
    for (let step = 0; step < 59; step++) {{
      const callback = pending.shift();
      now += delays.at(-1);
      callback();
    }}
    console.log(JSON.stringify({{ draws, now, delays }}));
    """


def run_clock(draw):
    return run_renderer_module("frame-clock.js", clock_run(draw))


def test_the_clock_holds_sixty_frames_each_second_despite_truncated_timers():
    result = run_clock("const drawFrame = () => { draws++; };")
    assert result["draws"] == 60
    assert abs(result["now"] - 59000 / 60) < 1e-6


def test_the_clock_survives_a_frame_that_throws():
    result = run_renderer_module(
        "frame-clock.js",
        """
        const pending = [];
        const clock = {
          performance: { now: () => 0 },
          setTimeout: (callback) => pending.push(callback),
        };
        try {
          rendererModule.startFrameClock(60, () => { throw new Error("frame"); }, clock);
        } catch {}
        console.log(JSON.stringify({ rescheduled: pending.length }));
        """,
    )
    assert result == {"rescheduled": 1}


def test_a_late_frame_does_not_burst_to_catch_up():
    result = run_clock(
        "const drawFrame = () => { draws++; if (draws === 1) now += 100; };"
    )
    assert result["delays"][0] == 0
    assert abs(result["delays"][1] - 1000 / 60) < 1e-6


STREAM = """
const reads = [];
const context = {
  RGBA: "rgba",
  UNSIGNED_BYTE: "byte",
  readPixels: (...read) => reads.push(read.slice(0, 6)),
};
const sent = [];
const stream = new rendererModule.CameraFrameStream(context, 4, 2, "ws://camera");
"""


def test_a_frame_is_read_as_rgba_and_sent_as_one_binary_message():
    result = run_renderer_module(
        "camera-frame-stream.js",
        STREAM
        + """
        stream.socket = { readyState: WebSocket.OPEN, bufferedAmount: 0, send: (pixels) => sent.push(pixels.length) };
        stream.sendFrame();
        console.log(JSON.stringify({ reads, sent }));
        """,
    )
    assert result == {"reads": [[0, 0, 4, 2, "rgba", "byte"]], "sent": [32]}


def test_no_pixels_are_read_while_the_camera_is_disconnected():
    result = run_renderer_module(
        "camera-frame-stream.js",
        STREAM
        + """
        stream.sendFrame();
        stream.socket = { readyState: WebSocket.CLOSED, bufferedAmount: 0, send: () => sent.push(1) };
        stream.sendFrame();
        console.log(JSON.stringify({ reads, sent }));
        """,
    )
    assert result == {"reads": [], "sent": []}


def test_a_frame_is_dropped_when_the_camera_falls_more_than_a_frame_behind():
    result = run_renderer_module(
        "camera-frame-stream.js",
        STREAM
        + """
        stream.socket = { readyState: WebSocket.OPEN, bufferedAmount: 33, send: () => sent.push(1) };
        stream.sendFrame();
        console.log(JSON.stringify({ reads, sent }));
        """,
    )
    assert result == {"reads": [], "sent": []}
