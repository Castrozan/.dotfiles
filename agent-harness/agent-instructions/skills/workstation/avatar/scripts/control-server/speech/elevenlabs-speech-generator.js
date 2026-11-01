const { spawn } = require("node:child_process");
const { spokenVowels } = require("./spoken-vowels");

const MODEL = "eleven_v4";
const REQUEST_TIMEOUT_MILLISECONDS = 15000;
const NATURAL_DELIVERY = "natural and conversational";
const EMOTION_DELIVERY = {
  happy: "warm and cheerful, smiling",
  excited: "excited and energetic",
  sad: "soft and sad",
  worried: "worried and hesitant",
  angry: "firm and angry",
  determined: "confident and determined",
  relaxed: "calm and relaxed",
  surprised: "surprised and amazed",
  thinking: "thoughtful and unhurried",
  shy: "shy and quiet",
  smug: "playful and teasing",
  sleepy: "sleepy and slow",
};

function runMediaSpeech(arguments_) {
  return new Promise((resolve, reject) => {
    const speech = spawn("media-speech", arguments_, {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    let failure = "";
    const timeout = setTimeout(
      () => speech.kill("SIGTERM"),
      REQUEST_TIMEOUT_MILLISECONDS,
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

function parseSpeechResult(output) {
  return JSON.parse(output.slice(output.indexOf("\n") + 1));
}

class ElevenLabsSpeechGenerator {
  constructor(defaultVoice, language) {
    this.defaultVoice = defaultVoice;
    this.language = language;
  }

  async generate(text, voice, emotion) {
    const result = parseSpeechResult(
      await runMediaSpeech([
        "generate",
        "--provider",
        "elevenlabs",
        "--model",
        MODEL,
        "--directions",
        EMOTION_DELIVERY[emotion] ?? NATURAL_DELIVERY,
        "--language",
        this.language,
        "--voice",
        voice || this.defaultVoice,
        "--text",
        text,
      ]),
    );
    return {
      audioPath: result.audio.path,
      duration: result.audio.duration_seconds,
      vowels:
        result.alignment.status === "available"
          ? spokenVowels(result.alignment)
          : [],
    };
  }
}

module.exports = { ElevenLabsSpeechGenerator, parseSpeechResult };
