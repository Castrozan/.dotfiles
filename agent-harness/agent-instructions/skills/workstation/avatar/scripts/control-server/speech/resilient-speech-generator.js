const { spokenLanguageOf } = require("./spoken-language");

const PIPER_VOICE_PATTERN = /^[a-z]{2}_[A-Z]{2}-/;
const KOKORO_VOICE_PATTERN = /^[a-z]{2}_[a-z]+$/;
const CLOUD_LANGUAGE_FOR_OTHER_SCRIPTS = "en-us";

class ResilientSpeechGenerator {
  constructor(
    cloudGenerator,
    kokoroGenerator,
    piperGenerator,
    homeLanguage,
    localVoices,
  ) {
    this.cloudGenerator = cloudGenerator;
    this.kokoroGenerator = kokoroGenerator;
    this.piperGenerator = piperGenerator;
    this.homeLanguage = homeLanguage;
    this.localVoices = localVoices;
  }

  generate(text, outputId, voice, emotion, settings = {}) {
    if (PIPER_VOICE_PATTERN.test(voice))
      return this.piperGenerator.generate(text, outputId, voice);
    if (KOKORO_VOICE_PATTERN.test(voice))
      return this.kokoroGenerator.generate(text, voice);
    const language = spokenLanguageOf(text, this.homeLanguage);
    return this.cloudGenerator
      .generate(
        text,
        voice,
        emotion,
        settings.model,
        language ?? CLOUD_LANGUAGE_FOR_OTHER_SCRIPTS,
      )
      .catch((error) => {
        const voices = this.localVoicesFor(language, settings.localVoice);
        if (!voices) throw error;
        console.error(`Cloud speech failed, using Kokoro: ${error.message}`);
        return this.generateLocally(text, outputId, language, voices);
      });
  }

  localVoicesFor(language, characterVoice) {
    const voices = this.localVoices[language];
    if (!voices || language !== this.homeLanguage) return voices;
    return { ...voices, kokoro: characterVoice || voices.kokoro };
  }

  generateLocally(text, outputId, language, voices) {
    return this.kokoroGenerator
      .generate(text, voices.kokoro, language)
      .catch((error) => {
        console.error(`Kokoro speech failed, using Piper: ${error.message}`);
        return this.piperGenerator.generate(text, outputId, voices.piper);
      });
  }
}

module.exports = { ResilientSpeechGenerator };
