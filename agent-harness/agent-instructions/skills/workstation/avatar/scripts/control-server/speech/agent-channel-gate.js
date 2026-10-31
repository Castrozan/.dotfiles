const { execFile } = require("node:child_process");

function runAvatarAudio(...commandArguments) {
  return new Promise((resolve, reject) => {
    execFile("avatar-audio", commandArguments, (error, stdout) =>
      error ? reject(error) : resolve(stdout),
    );
  });
}

class AgentChannelGate {
  async open() {
    const status = JSON.parse(await runAvatarAudio("status"));
    if (!status.running) {
      throw new Error("Avatar audio is not running; run avatar-start");
    }
    if (!status.channels.agent.mute) return async () => {};
    await runAvatarAudio("mute", "agent", "0");
    return () => runAvatarAudio("mute", "agent", "1");
  }
}

module.exports = { AgentChannelGate };
