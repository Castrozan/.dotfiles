const { spawn } = require("child_process");
const fs = require("fs").promises;
const path = require("path");

const VOICE_NAME_PATTERN = /^[A-Za-z0-9_-]+$/;
const WAV_BYTE_RATE_OFFSET = 28;
const WAV_HEADER_BYTES = 44;

function runPiper(modelPath, audioPath, text) {
  return new Promise((resolve, reject) => {
    const piper = spawn(
      "piper",
      ["--model", modelPath, "--output_file", audioPath],
      { stdio: ["pipe", "ignore", "pipe"] },
    );
    piper.stderr.on("data", () => {});
    piper.on("close", (exitCode) =>
      exitCode === 0
        ? resolve()
        : reject(new Error(`piper exited ${exitCode}`)),
    );
    piper.on("error", reject);
    piper.stdin.end(text);
  });
}

function wavDurationSeconds(audio) {
  const byteRate = audio.readUInt32LE(WAV_BYTE_RATE_OFFSET);
  return (audio.length - WAV_HEADER_BYTES) / byteRate;
}

class TextToSpeechGenerator {
  constructor(outputRootDirectory, defaultVoice, voiceModelDirectory) {
    this.outputRootDirectory = outputRootDirectory;
    this.defaultVoice = defaultVoice;
    this.voiceModelDirectory = voiceModelDirectory;
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
    const voice = voiceOverride || this.defaultVoice;
    if (!VOICE_NAME_PATTERN.test(voice)) {
      throw new Error(`Unknown voice: ${voice}`);
    }
    const outputDirectory = path.join(this.outputRootDirectory, outputId);
    const audioPath = path.join(outputDirectory, "voice.wav");
    const modelPath = path.join(this.voiceModelDirectory, `${voice}.onnx`);
    await fs.mkdir(outputDirectory, { recursive: true });
    await runPiper(modelPath, audioPath, text);
    return {
      audioPath,
      duration: wavDurationSeconds(await fs.readFile(audioPath)),
    };
  }
}

module.exports = { TextToSpeechGenerator };
