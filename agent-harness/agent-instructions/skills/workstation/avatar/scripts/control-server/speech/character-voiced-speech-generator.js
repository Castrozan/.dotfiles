class CharacterVoicedSpeechGenerator {
  constructor(speechGenerator, characters) {
    this.speechGenerator = speechGenerator;
    this.characters = characters;
    this.selected = characters[0];
  }

  selectCharacter(name) {
    const character = this.characters.find(
      (candidate) => candidate.name === name,
    );
    if (!character) return false;
    this.selected = character;
    return true;
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
