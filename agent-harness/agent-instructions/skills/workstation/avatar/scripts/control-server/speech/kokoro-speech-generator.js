const { runMediaSpeech } = require("./media-speech-client");

const REQUEST_TIMEOUT_MILLISECONDS = 30000;

class KokoroSpeechGenerator {
  constructor(defaultVoice, language) {
    this.defaultVoice = defaultVoice;
    this.language = language;
  }

  async generate(text, voice, language = this.language) {
    const result = await runMediaSpeech(
      [
        "generate",
        "--provider",
        "kokoro",
        "--language",
        language,
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
      vowels: [],
      source: "kokoro",
    };
  }
}

module.exports = { KokoroSpeechGenerator };
