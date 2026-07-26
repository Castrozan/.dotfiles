const { spawn } = require("child_process");

function buildPulseAudioEnvironment() {
  return {
    ...process.env,
    XDG_RUNTIME_DIR: `/run/user/${process.getuid()}`,
  };
}

function playAudioFileToSink(audioPath, sinkName) {
  const environment = buildPulseAudioEnvironment();

  const decoder = spawn(
    "ffmpeg",
    [
      "-y",
      "-i",
      audioPath,
      "-f",
      "s16le",
      "-ar",
      "48000",
      "-ac",
      "2",
      "pipe:1",
    ],
    { stdio: ["ignore", "pipe", "pipe"], env: environment },
  );

  const player = spawn(
    "paplay",
    ["--device", sinkName, "--raw", "--rate", "48000", "--channels", "2"],
    { stdio: [decoder.stdout, "ignore", "pipe"], env: environment },
  );

  decoder.stderr.on("data", (chunk) => {
    const line = chunk.toString().trim();
    if (line.toLowerCase().includes("error")) {
      console.error(`🔊 Audio decode error (${sinkName}): ${line}`);
    }
  });

  player.stderr.on("data", (chunk) => {
    console.error(`🔊 paplay error (${sinkName}): ${chunk.toString().trim()}`);
  });

  player.on("close", (exitCode) => {
    console.log(`🔊 paplay finished (${sinkName}), exit code: ${exitCode}`);
  });

  decoder.on("close", (exitCode) => {
    console.log(
      `🔊 ffmpeg decode finished (${sinkName}), exit code: ${exitCode}`,
    );
  });

  return player;
}

module.exports = { playAudioFileToSink };
