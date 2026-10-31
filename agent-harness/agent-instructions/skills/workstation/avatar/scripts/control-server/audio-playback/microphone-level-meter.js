const { spawn } = require("node:child_process");

function measureLevel(samples) {
  let power = 0;
  const count = Math.floor(samples.length / 4);
  for (let index = 0; index < count; index++) {
    const value = samples.readFloatLE(index * 4);
    if (Number.isFinite(value)) power += value * value;
  }
  return count ? Math.sqrt(power / count) : 0;
}

function startMicrophoneLevelMeter(clientRegistry, sourceName) {
  const recorder = spawn(
    "parec",
    [
      "--device",
      sourceName,
      "--property=node.dont-reconnect=true",
      "--raw",
      "--format=float32le",
      "--rate=48000",
      "--channels=1",
      "--latency-msec=20",
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  let pending = Buffer.alloc(0);
  let level = 0;
  recorder.stdout.on("data", (chunk) => {
    const samples = Buffer.concat([pending, chunk]);
    const alignedSize = samples.length - (samples.length % 4);
    level = measureLevel(samples.subarray(0, alignedSize));
    pending = Buffer.from(samples.subarray(alignedSize));
  });
  const interval = setInterval(() => {
    clientRegistry.sendToRenderer({ type: "audioLevel", level });
    level = 0;
  }, 33);
  const silence = () => {
    clearInterval(interval);
    clientRegistry.sendToRenderer({ type: "audioLevel", level: 0 });
  };
  recorder.on("error", (error) => {
    console.error(error.message);
    silence();
  });
  recorder.on("close", silence);
  recorder.stderr.on("data", (chunk) => console.error(chunk.toString().trim()));
  return () => {
    silence();
    recorder.kill("SIGTERM");
  };
}

module.exports = { measureLevel, startMicrophoneLevelMeter };
