const { readFileSync } = require("node:fs");
const {
  CharacterVoicedSpeechGenerator,
} = require("./character-voiced-speech-generator");
const { TextToSpeechGenerator } = require("./text-to-speech-generator");
const { KokoroSpeechGenerator } = require("./kokoro-speech-generator");
const { ElevenLabsSpeechGenerator } = require("./elevenlabs-speech-generator");
const { ResilientSpeechGenerator } = require("./resilient-speech-generator");

function localVoicesByLanguage(config) {
  return {
    "pt-br": { kokoro: config.KOKORO_VOICE, piper: config.TTS_VOICE },
    "en-us": {
      kokoro: config.KOKORO_ENGLISH_VOICE,
      piper: config.TTS_ENGLISH_VOICE,
    },
  };
}

async function assembleSpeechGenerator(config) {
  const localSpeechGenerator = new TextToSpeechGenerator(
    config.TTS_DIR,
    config.TTS_VOICE,
    config.TTS_VOICE_DIRECTORY,
  );
  await localSpeechGenerator.prepareOutputRootDirectory();
  return new CharacterVoicedSpeechGenerator(
    new ResilientSpeechGenerator(
      new ElevenLabsSpeechGenerator(
        config.CLOUD_VOICE,
        config.CLOUD_VOICE_LANGUAGE,
      ),
      new KokoroSpeechGenerator(
        config.KOKORO_VOICE,
        config.CLOUD_VOICE_LANGUAGE,
      ),
      localSpeechGenerator,
      config.CLOUD_VOICE_LANGUAGE,
      localVoicesByLanguage(config),
    ),
    JSON.parse(readFileSync(config.CHARACTER_VOICES_PATH, "utf8")),
  );
}

module.exports = { assembleSpeechGenerator };
