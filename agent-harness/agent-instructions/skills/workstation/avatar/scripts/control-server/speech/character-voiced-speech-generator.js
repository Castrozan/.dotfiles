class CharacterVoicedSpeechGenerator {
  constructor(speechGenerator, characters) {
    this.speechGenerator = speechGenerator;
    this.characters = characters;
    this.selected = characters[0];
  }

  selectCharacter(name) {
    this.selected =
      this.characters.find((character) => character.name === name) ??
      this.selected;
  }

  generate(text, outputId, voice, emotion, model) {
    return this.speechGenerator.generate(
      text,
      outputId,
      voice || this.selected.cloudVoice,
      emotion,
      { localVoice: this.selected.localVoice, model },
    );
  }
}

module.exports = { CharacterVoicedSpeechGenerator };
