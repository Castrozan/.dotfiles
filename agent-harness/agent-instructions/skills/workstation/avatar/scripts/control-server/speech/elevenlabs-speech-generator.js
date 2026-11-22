const { runMediaSpeech } = require("./media-speech-client");
const { spokenVowels } = require("./spoken-vowels");

const MODEL = "eleven_v4";
const SHORT_REQUEST_TIMEOUT_MILLISECONDS = 15000;
const REQUEST_TIMEOUT_MILLISECONDS_PER_CHARACTER = 30;
const LONGEST_REQUEST_TIMEOUT_MILLISECONDS = 120000;
const NATURAL_DELIVERY = "natural and conversational";
const EMOTION_DELIVERY = require("./emotion-delivery.json");

function requestTimeoutMilliseconds(text) {
  return Math.min(
    SHORT_REQUEST_TIMEOUT_MILLISECONDS +
      REQUEST_TIMEOUT_MILLISECONDS_PER_CHARACTER * text.length,
    LONGEST_REQUEST_TIMEOUT_MILLISECONDS,
  );
}

class ElevenLabsSpeechGenerator {
  constructor(defaultVoice, language) {
    this.defaultVoice = defaultVoice;
    this.language = language;
  }

  async generate(
    text,
    voice,
    emotion,
    model = MODEL,
    language = this.language,
  ) {
    const result = await runMediaSpeech(
      [
        "generate",
        "--provider",
        "elevenlabs",
        "--model",
        model,
        ...(model === MODEL
          ? ["--directions", EMOTION_DELIVERY[emotion] ?? NATURAL_DELIVERY]
          : []),
        "--language",
        language,
        "--voice",
        voice || this.defaultVoice,
        "--text",
        text,
      ],
      requestTimeoutMilliseconds(text),
    );
    return {
      audioPath: result.audio.path,
      duration: result.audio.duration_seconds,
      vowels:
        result.alignment.status === "available"
          ? spokenVowels(result.alignment)
          : [],
      source: "elevenlabs",
    };
  }
}

module.exports = { ElevenLabsSpeechGenerator };
