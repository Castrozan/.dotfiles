const { runMediaSpeech } = require("./media-speech-client");
const { spokenVowels } = require("./spoken-vowels");

const MODEL = "eleven_v4";
const REQUEST_TIMEOUT_MILLISECONDS = 15000;
const NATURAL_DELIVERY = "natural and conversational";
const EMOTION_DELIVERY = require("./emotion-delivery.json");

class ElevenLabsSpeechGenerator {
  constructor(defaultVoice, language) {
    this.defaultVoice = defaultVoice;
    this.language = language;
  }

  async generate(text, voice, emotion, model = MODEL) {
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
        this.language,
        "--voice",
        voice || this.defaultVoice,
        "--text",
        text,
      ],
      REQUEST_TIMEOUT_MILLISECONDS,
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
