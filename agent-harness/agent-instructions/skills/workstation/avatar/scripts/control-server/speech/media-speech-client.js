const { spawn } = require("node:child_process");

function readMediaSpeechOutput(arguments_, timeoutMilliseconds) {
  return new Promise((resolve, reject) => {
    const speech = spawn("media-speech", arguments_, {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    let failure = "";
    const timeout = setTimeout(
      () => speech.kill("SIGTERM"),
      timeoutMilliseconds,
    );
    speech.stdout.on("data", (chunk) => (output += chunk));
    speech.stderr.on("data", (chunk) => (failure += chunk));
    speech.on("error", reject);
    speech.on("close", (exitCode) => {
      clearTimeout(timeout);
      if (exitCode === 0) resolve(output);
      else reject(new Error(`media-speech failed: ${failure.trim()}`));
    });
  });
}

async function runMediaSpeech(arguments_, timeoutMilliseconds) {
  return JSON.parse(
    await readMediaSpeechOutput(arguments_, timeoutMilliseconds),
  );
}

module.exports = { runMediaSpeech };
