const { spawn } = require("child_process");

const PLAYBACK_CLIENT_NAME = "avatar-speech";

function buildPulseAudioEnvironment() {
  return {
    ...process.env,
    XDG_RUNTIME_DIR: `/run/user/${process.getuid()}`,
  };
}

function playAudioFileToSink(audioPath, sinkName) {
  const player = spawn(
    "paplay",
    ["--client-name", PLAYBACK_CLIENT_NAME, "--device", sinkName, audioPath],
    { stdio: ["ignore", "ignore", "pipe"], env: buildPulseAudioEnvironment() },
  );

  player.stderr.on("data", (chunk) => {
    console.error(`🔊 paplay error (${sinkName}): ${chunk.toString().trim()}`);
  });

  return {
    finished: new Promise((resolve) => {
      player.on("close", resolve);
      player.on("error", resolve);
    }),
    stop: () => player.kill("SIGTERM"),
  };
}

module.exports = { playAudioFileToSink };
