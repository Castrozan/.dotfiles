const { spawn } = require("node:child_process");
const fileSystem = require("node:fs");

const LEVEL_INTERVAL_MILLISECONDS = 33;
const LEVEL_WINDOW_SECONDS = LEVEL_INTERVAL_MILLISECONDS / 1000;
const SOUND_DELAY_SECONDS = 0.3;
const SAMPLE_RATE_OFFSET = 24;
const DATA_HEADER_BYTES = 8;
const BYTES_PER_SAMPLE = 2;
const FULL_SCALE = 32768;

function recordingOf(wave) {
  const data = wave.indexOf("data");
  return {
    rate: wave.readUInt32LE(SAMPLE_RATE_OFFSET),
    samples: wave.subarray(data + DATA_HEADER_BYTES),
  };
}

function levelAt({ rate, samples }, seconds) {
  const first = Math.floor(seconds * rate);
  const count = Math.floor(LEVEL_WINDOW_SECONDS * rate);
  const total = Math.floor(samples.length / BYTES_PER_SAMPLE);
  if (first < 0 || first >= total) return 0;
  const last = Math.min(first + count, total);
  let power = 0;
  for (let index = first; index < last; index++) {
    const value = samples.readInt16LE(index * BYTES_PER_SAMPLE) / FULL_SCALE;
    power += value * value;
  }
  return Math.sqrt(power / (last - first));
}

function playThroughProgram(
  [program, ...programArguments],
  sendVoiceLevel,
  now = Date.now,
) {
  return (audioPath) => {
    const recording = recordingOf(fileSystem.readFileSync(audioPath));
    const player = spawn(program, [...programArguments, audioPath], {
      stdio: ["ignore", "ignore", "pipe"],
    });
    player.stderr.on("data", (chunk) =>
      console.error(`${program}: ${chunk.toString().trim()}`),
    );
    const started = now();
    const levels = setInterval(() => {
      const heardSeconds = (now() - started) / 1000 - SOUND_DELAY_SECONDS;
      sendVoiceLevel(levelAt(recording, heardSeconds));
    }, LEVEL_INTERVAL_MILLISECONDS);
    const ended = new Promise((resolve) => {
      player.on("close", resolve);
      player.on("error", resolve);
    });
    return {
      finished: ended.then(() => {
        clearInterval(levels);
        sendVoiceLevel(0);
      }),
      stop: () => player.kill("SIGTERM"),
    };
  };
}

module.exports = { levelAt, playThroughProgram, recordingOf };
