const PIPER_VOICE_PATTERN = /^[a-z]{2}_[A-Z]{2}-/;
const KOKORO_VOICE_PATTERN = /^[a-z]{2}_[a-z]+$/;

class ResilientSpeechGenerator {
  constructor(cloudGenerator, kokoroGenerator, piperGenerator) {
    this.cloudGenerator = cloudGenerator;
    this.kokoroGenerator = kokoroGenerator;
    this.piperGenerator = piperGenerator;
  }

  generate(text, outputId, voice, emotion) {
    if (PIPER_VOICE_PATTERN.test(voice))
      return this.piperGenerator.generate(text, outputId, voice);
    if (KOKORO_VOICE_PATTERN.test(voice))
      return this.kokoroGenerator.generate(text, voice);
    return this.cloudGenerator.generate(text, voice, emotion).catch((error) => {
      console.error(`Cloud speech failed, using Kokoro: ${error.message}`);
      return this.generateLocally(text, outputId);
    });
  }

  generateLocally(text, outputId) {
    return this.kokoroGenerator.generate(text).catch((error) => {
      console.error(`Kokoro speech failed, using Piper: ${error.message}`);
      return this.piperGenerator.generate(text, outputId);
    });
  }
}

module.exports = { ResilientSpeechGenerator };
