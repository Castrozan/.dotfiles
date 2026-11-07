const { spawn } = require("node:child_process");

const STACK_DUMP_MILLISECONDS = 500;

function stopWithStackDump(speech) {
  speech.kill("SIGUSR1");
  setTimeout(() => speech.kill("SIGTERM"), STACK_DUMP_MILLISECONDS);
}

function readMediaSpeechOutput(arguments_, timeoutMilliseconds) {
  return new Promise((resolve, reject) => {
    const speech = spawn("media-speech", arguments_, {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    let failure = "";
    const timeout = setTimeout(
      () => stopWithStackDump(speech),
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
