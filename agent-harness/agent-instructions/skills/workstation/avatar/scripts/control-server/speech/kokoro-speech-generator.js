const { parseSpeechResult, runMediaSpeech } = require("./media-speech-client");

const REQUEST_TIMEOUT_MILLISECONDS = 30000;

class KokoroSpeechGenerator {
  constructor(defaultVoice, language) {
    this.defaultVoice = defaultVoice;
    this.language = language;
  }

  async generate(text, voice) {
    const result = parseSpeechResult(
      await runMediaSpeech(
        [
          "generate",
          "--provider",
          "kokoro",
          "--language",
          this.language,
          "--voice",
          voice || this.defaultVoice,
          "--text",
          text,
        ],
        REQUEST_TIMEOUT_MILLISECONDS,
      ),
    );
    return {
      audioPath: result.audio.path,
      duration: result.audio.duration_seconds,
      vowels: [],
    };
  }
}

module.exports = { KokoroSpeechGenerator };
