const LOCAL_VOICE_PATTERN = /^[a-z]{2}_[A-Z]{2}-/;

class ResilientSpeechGenerator {
  constructor(cloudGenerator, localGenerator) {
    this.cloudGenerator = cloudGenerator;
    this.localGenerator = localGenerator;
  }

  async generate(text, outputId, voice, emotion) {
    if (LOCAL_VOICE_PATTERN.test(voice ?? ""))
      return this.localGenerator.generate(text, outputId, voice);
    try {
      return await this.cloudGenerator.generate(text, voice, emotion);
    } catch (error) {
      console.error(`Cloud speech failed, using local voice: ${error.message}`);
      return this.localGenerator.generate(text, outputId);
    }
  }
}

module.exports = { ResilientSpeechGenerator };
