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

function shapesOutsideDeliveryTags(characters) {
  let insideDeliveryTag = false;
  return characters.map((character) => {
    if (character === "[") insideDeliveryTag = true;
    const shape = insideDeliveryTag ? null : vowelShape(character);
    if (character === "]") insideDeliveryTag = false;
    return shape;
  });
}

function spokenVowels({ characters, starts_seconds, ends_seconds }) {
  return shapesOutsideDeliveryTags(characters).flatMap((shape, index) =>
    shape
      ? [{ shape, start: starts_seconds[index], end: ends_seconds[index] }]
      : [],
  );
}

module.exports = { spokenVowels };
