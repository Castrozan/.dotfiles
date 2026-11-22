const MAXIMUM_CHUNK_CHARACTERS = 200;
const CLAUSE_END = /(?<=[,;:–—]\s+|[、，；：])(?=\S)/u;
const WORD_START = /(?<=\s)(?=\S)/u;

function segmentsOf(granularity) {
  const segmenter = new Intl.Segmenter(undefined, { granularity });
  return (text) =>
    Array.from(segmenter.segment(text), ({ segment }) => segment);
}

const SPLITTERS_FROM_WIDEST = [
  segmentsOf("sentence"),
  (text) => text.split(CLAUSE_END),
  (text) => text.split(WORD_START),
  segmentsOf("grapheme"),
  (text) => Array.from(text),
];

function packed(pieces, maximumCharacters) {
  const chunks = [];
  for (const piece of pieces) {
    const last = chunks.length - 1;
    if (last >= 0 && chunks[last].length + piece.length <= maximumCharacters)
      chunks[last] += piece;
    else chunks.push(piece);
  }
  return chunks;
}

function chunksAtLevel(text, maximumCharacters, level) {
  if (text.length <= maximumCharacters) return [text];
  const pieces = SPLITTERS_FROM_WIDEST[level](text).flatMap((piece) =>
    chunksAtLevel(piece, maximumCharacters, level + 1),
  );
  return packed(pieces, maximumCharacters);
}

function speechChunks(text, maximumCharacters = MAXIMUM_CHUNK_CHARACTERS) {
  return chunksAtLevel(text, maximumCharacters, 0);
}

module.exports = { MAXIMUM_CHUNK_CHARACTERS, speechChunks };
