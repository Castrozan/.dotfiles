const { spawn } = require("child_process");
const fs = require("fs").promises;
const path = require("path");
const { parseSpeechTiming } = require("./speech-timing-parser");

function runEdgeTextToSpeech(commandArguments) {
  return new Promise((resolve, reject) => {
    const edgeTextToSpeechProcess = spawn("edge-tts", commandArguments, {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let diagnostics = "";
    edgeTextToSpeechProcess.stderr.on("data", (chunk) => {
      diagnostics = (diagnostics + chunk.toString()).slice(-8192);
    });
    edgeTextToSpeechProcess.on("close", (exitCode) =>
      exitCode === 0
        ? resolve()
        : reject(textToSpeechFailure(exitCode, diagnostics)),
    );
    edgeTextToSpeechProcess.on("error", reject);
  });
}

function textToSpeechFailure(exitCode, diagnostics) {
  const rejected = diagnostics.match(/WSServerHandshakeError:\s*(\d{3})/);
  return new Error(
    rejected
      ? `edge-tts returned HTTP ${rejected[1]}`
      : `edge-tts exited ${exitCode}`,
  );
}

class TextToSpeechGenerator {
  constructor(outputRootDirectory, defaultVoice) {
    this.outputRootDirectory = outputRootDirectory;
    this.defaultVoice = defaultVoice;
  }

  async prepareOutputRootDirectory() {
    try {
      await fs.mkdir(this.outputRootDirectory, {
        recursive: true,
        mode: 0o700,
      });
      console.log(`✅ TTS directory: ${this.outputRootDirectory}`);
    } catch (error) {
      console.error("❌ Failed to create TTS directory:", error.message);
    }
  }

  async generate(text, outputId, voiceOverride = null) {
    const outputDirectory = path.join(this.outputRootDirectory, outputId);
    const audioPath = path.join(outputDirectory, "voice.mp3");
    const timingPath = path.join(outputDirectory, "timing.json");

    try {
      await fs.mkdir(outputDirectory, { recursive: true });

      console.log(
        `🎤 Generating TTS: "${text.substring(0, 50)}${text.length > 50 ? "..." : ""}"`,
      );
      await runEdgeTextToSpeech([
        "--text",
        text,
        "--voice",
        voiceOverride || this.defaultVoice,
        "--rate",
        "+0%",
        "--write-media",
        audioPath,
        "--write-subtitles",
        timingPath,
      ]);

      const timing = parseSpeechTiming(await fs.readFile(timingPath, "utf-8"));

      return {
        audioPath,
        audioUrl: `/audio/${outputId}/voice.mp3`,
        timing,
        duration: timing.length > 0 ? timing[timing.length - 1].end : 0,
      };
    } catch (error) {
      console.error("❌ TTS generation failed:", error.message);
      throw error;
    }
  }
}

module.exports = { TextToSpeechGenerator };
