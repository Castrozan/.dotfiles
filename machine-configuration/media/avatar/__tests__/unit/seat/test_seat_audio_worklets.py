import json
import subprocess
from pathlib import Path

WORKLETS = (
    Path(__file__).resolve().parents[3]
    / "scripts/conversation/remote_seat/page/seat-audio-worklets.js"
)
RENDER_QUANTUM = 128


def run_worklet(sample_rate, body):
    program = f"""
    const registered = {{}};
    globalThis.sampleRate = {sample_rate};
    globalThis.AudioWorkletProcessor = class {{
      constructor() {{
        this.port = {{ posted: [], postMessage(message) {{ this.posted.push(message); }} }};
      }}
    }};
    globalThis.registerProcessor = (name, processor) => {{ registered[name] = processor; }};
    const render = (processor, quanta) => {{
      const played = [];
      for (let quantum = 0; quantum < quanta; quantum++) {{
        const output = new Float32Array({RENDER_QUANTUM});
        processor.process([], [[output]]);
        played.push(...output);
      }}
      return played.map((sample) => Math.round(sample * 32767));
    }};
    const ramp = (first, length) => Int16Array.from({{ length }}, (_, index) => first + index);
    import("file://{WORKLETS}").then(() => {{
      {body}
    }}).catch(error => {{ console.error(error); process.exitCode = 1; }});
    """
    completed = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(completed.stdout)


def test_the_microphone_leaves_in_whole_clamped_twenty_millisecond_frames():
    result = run_worklet(
        16000,
        f"""
        const microphone = new registered["microphone-frames"]();
        const samples = Float32Array.from({{ length: 1000 }}, (_, index) => index / 1000);
        samples[0] = 4;
        samples[1] = -4;
        for (let start = 0; start < samples.length; start += {RENDER_QUANTUM})
          microphone.process([[samples.subarray(start, start + {RENDER_QUANTUM})]]);
        const frames = microphone.port.posted.map((buffer) => [...new Int16Array(buffer)]);
        console.log(JSON.stringify({{ lengths: frames.map((frame) => frame.length), sent: frames.flat() }}));
        """,
    )
    assert result["lengths"] == [320, 320, 320]
    assert result["sent"][:2] == [32767, -32767]
    assert result["sent"][2:] == [int(index / 1000 * 32767) for index in range(2, 960)]


def test_the_voice_waits_for_a_cushion_then_plays_every_sample_once_in_order():
    result = run_worklet(
        24000,
        """
        const voice = new registered["voice-playback"]();
        voice.port.onmessage({ data: ramp(1, 2400).buffer });
        const early = render(voice, 4);
        voice.port.onmessage({ data: ramp(2401, 2400).buffer });
        const played = render(voice, 40);
        console.log(JSON.stringify({ early, played }));
        """,
    )
    assert set(result["early"]) == {0}
    assert [sample for sample in result["played"] if sample] == list(range(1, 4801))


def test_the_voice_cushions_again_after_running_dry():
    result = run_worklet(
        24000,
        """
        const voice = new registered["voice-playback"]();
        voice.port.onmessage({ data: ramp(1, 3000).buffer });
        render(voice, 30);
        voice.port.onmessage({ data: ramp(1, 480).buffer });
        const starved = render(voice, 4);
        console.log(JSON.stringify({ starved }));
        """,
    )
    assert set(result["starved"]) == {0}


def test_a_stalled_network_never_delays_the_voice_past_its_limit():
    result = run_worklet(
        24000,
        """
        const voice = new registered["voice-playback"]();
        for (let burst = 0; burst < 100; burst++)
          voice.port.onmessage({ data: new Int16Array(480).fill(burst + 1).buffer });
        const played = render(voice, 200).filter((sample) => sample);
        console.log(JSON.stringify({ queued: played.length, last: played.at(-1) }));
        """,
    )
    assert result["queued"] <= 24000 * 0.6
    assert result["last"] == 100


def test_silence_is_dropped_while_the_voice_runs_behind():
    result = run_worklet(
        24000,
        """
        const voice = new registered["voice-playback"]();
        voice.port.onmessage({ data: ramp(1, 4800).buffer });
        voice.port.onmessage({ data: new Int16Array(4800).buffer });
        voice.port.onmessage({ data: ramp(4801, 480).buffer });
        const played = render(voice, 60);
        console.log(JSON.stringify({ played: played.slice(0, 5280) }));
        """,
    )
    assert result["played"] == list(range(1, 5281))


def test_the_voice_reports_how_much_it_holds_ten_times_a_second():
    result = run_worklet(
        24000,
        """
        const voice = new registered["voice-playback"]();
        voice.port.onmessage({ data: ramp(1, 7200).buffer });
        render(voice, 60);
        console.log(JSON.stringify({ reports: voice.port.posted }));
        """,
    )
    held = [report["queuedSeconds"] for report in result["reports"]]
    assert len(held) == 60 * RENDER_QUANTUM // 2400
    played_before_first_report = 18 * RENDER_QUANTUM
    assert held[0] == (7200 - played_before_first_report) / 24000
    assert held == sorted(held, reverse=True)
