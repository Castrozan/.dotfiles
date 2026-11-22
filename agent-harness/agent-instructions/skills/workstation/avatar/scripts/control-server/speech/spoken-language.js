const FUNCTION_WORDS = require("./language-function-words.json");

const PORTUGUESE = "pt-br";
const ENGLISH = "en-us";
const LATIN_LETTER = /\p{Script=Latin}/u;
const ANY_LETTER = /\p{L}/u;
const WORD = /[\p{L}']+/gu;
const PORTUGUESE_ONLY_LETTERS = /[ãõçáàâéêíóôú]/giu;
const VOCABULARIES = Object.fromEntries(
  Object.entries(FUNCTION_WORDS).map(([language, words]) => [
    language,
    new Set(words),
  ]),
);

function dominatedByOtherScripts(text) {
  const letters = [...text].filter((character) => ANY_LETTER.test(character));
  const latinLetters = letters.filter((character) =>
    LATIN_LETTER.test(character),
  );
  return letters.length - latinLetters.length > latinLetters.length;
}

function vocabularyHits(words, language) {
  return words.filter((word) => VOCABULARIES[language].has(word)).length;
}

function evidenceFor(text) {
  const words = text.toLowerCase().replaceAll("’", "'").match(WORD) ?? [];
  const accents = text.match(PORTUGUESE_ONLY_LETTERS) ?? [];
  return {
    [PORTUGUESE]: vocabularyHits(words, PORTUGUESE) + accents.length,
    [ENGLISH]: vocabularyHits(words, ENGLISH),
  };
}

function spokenLanguageOf(text, homeLanguage) {
  if (dominatedByOtherScripts(text)) return null;
  const evidence = evidenceFor(text);
  if (evidence[PORTUGUESE] === evidence[ENGLISH]) return homeLanguage;
  return evidence[PORTUGUESE] > evidence[ENGLISH] ? PORTUGUESE : ENGLISH;
}

module.exports = { spokenLanguageOf };
