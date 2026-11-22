const { spokenLanguageOf } = require("./spoken-language");

const MAXIMUM_CHUNK_CHARACTERS = 200;
const UNDECIDED = "undecided";
const CLAUSE_END = /(?<=[,;:–—]\s+|[、，；：])(?=\S)/u;
const WORD_START = /(?<=\s)(?=\S)/u;

function segmentsOf(granularity) {
  const segmenter = new Intl.Segmenter(undefined, { granularity });
  return (text) =>
    Array.from(segmenter.segment(text), ({ segment }) => segment);
}

const sentencesOf = segmentsOf("sentence");

const SPLITTERS_WITHIN_A_SENTENCE = [
  (text) => text.split(CLAUSE_END),
  (text) => text.split(WORD_START),
  segmentsOf("grapheme"),
  (text) => Array.from(text),
];

function languageOfSentence(sentence) {
  const language = spokenLanguageOf(sentence, "pt-br");
  return language === spokenLanguageOf(sentence, "en-us")
    ? language
    : UNDECIDED;
}

function languagesJoin(chunkLanguage, pieceLanguage) {
  if (chunkLanguage === pieceLanguage) return true;
  const bothLatin = chunkLanguage !== null && pieceLanguage !== null;
  return bothLatin && [chunkLanguage, pieceLanguage].includes(UNDECIDED);
}

function joins(chunk, piece, maximumCharacters) {
  return (
    chunk.text.length + piece.text.length <= maximumCharacters &&
    languagesJoin(chunk.language, piece.language)
  );
}

function joinInto(chunk, piece) {
  chunk.text += piece.text;
  if (chunk.language === UNDECIDED) chunk.language = piece.language;
}

function packed(pieces, maximumCharacters) {
  const chunks = [];
  for (const piece of pieces) {
    const last = chunks.at(-1);
    if (last && joins(last, piece, maximumCharacters)) joinInto(last, piece);
    else chunks.push({ ...piece });
  }
  return chunks;
}

function partsOfSentence(piece, maximumCharacters, level) {
  if (piece.text.length <= maximumCharacters) return [piece];
  const parts = SPLITTERS_WITHIN_A_SENTENCE[level](piece.text).flatMap((text) =>
    partsOfSentence(
      { text, language: piece.language },
      maximumCharacters,
      level + 1,
    ),
  );
  return packed(parts, maximumCharacters);
}

function speechChunks(text, maximumCharacters = MAXIMUM_CHUNK_CHARACTERS) {
  const sentences = sentencesOf(text).flatMap((sentence) =>
    partsOfSentence(
      { text: sentence, language: languageOfSentence(sentence) },
      maximumCharacters,
      0,
    ),
  );
  return packed(sentences, maximumCharacters).map(({ text }) => text);
}

module.exports = { MAXIMUM_CHUNK_CHARACTERS, speechChunks };
