const VOWEL_SHAPES = {
  a: "aa",
  e: "ee",
  i: "ih",
  y: "ih",
  o: "oh",
  u: "ou",
};

function vowelShape(character) {
  const base = character.normalize("NFD")[0].toLowerCase();
  return VOWEL_SHAPES[base] ?? null;
}

function spokenVowels({ characters, starts_seconds, ends_seconds }) {
  const vowels = [];
  let insideDeliveryTag = false;
  characters.forEach((character, index) => {
    if (character === "[") insideDeliveryTag = true;
    const shape = insideDeliveryTag ? null : vowelShape(character);
    if (character === "]") insideDeliveryTag = false;
    if (shape)
      vowels.push({
        shape,
        start: starts_seconds[index],
        end: ends_seconds[index],
      });
  });
  return vowels;
}

module.exports = { spokenVowels };
