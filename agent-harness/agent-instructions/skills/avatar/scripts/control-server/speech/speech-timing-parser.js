const SUBTITLE_TIMESTAMP_PATTERN =
  /(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})/;

function approximatePhoneme(word) {
  if (!word) {
    return "neutral";
  }
  return word.toLowerCase().match(/[aeiou]/)?.[0] || "neutral";
}

function toSeconds(hours, minutes, seconds, milliseconds) {
  return (
    parseInt(hours) * 3600 +
    parseInt(minutes) * 60 +
    parseInt(seconds) +
    parseInt(milliseconds) / 1000
  );
}

function parseSubtitleBlock(block) {
  const lines = block.trim().split("\n");
  if (lines.length < 2) {
    return null;
  }

  const timestampLine = lines.find((line) => line.includes("-->"));
  if (!timestampLine) {
    return null;
  }

  const timestampMatch = timestampLine.match(SUBTITLE_TIMESTAMP_PATTERN);
  if (!timestampMatch) {
    return null;
  }

  const text = lines
    .slice(lines.indexOf(timestampLine) + 1)
    .join(" ")
    .trim();
  if (!text) {
    return null;
  }

  return {
    start: toSeconds(
      timestampMatch[1],
      timestampMatch[2],
      timestampMatch[3],
      timestampMatch[4],
    ),
    end: toSeconds(
      timestampMatch[5],
      timestampMatch[6],
      timestampMatch[7],
      timestampMatch[8],
    ),
    text,
  };
}

function splitBlockIntoWordTimings({ start, end, text }) {
  const words = text.split(/\s+/);
  const wordDuration = (end - start) / words.length;
  return words.map((word, wordIndex) => ({
    start: start + wordIndex * wordDuration,
    end: start + (wordIndex + 1) * wordDuration,
    text: word,
    phoneme: approximatePhoneme(word),
  }));
}

function parseSpeechTiming(subtitleData) {
  try {
    return subtitleData
      .trim()
      .split(/\n\n+/)
      .map(parseSubtitleBlock)
      .filter((block) => block !== null)
      .flatMap(splitBlockIntoWordTimings);
  } catch (error) {
    console.warn("⚠️ Failed to parse timing data:", error.message);
    return [];
  }
}

module.exports = { parseSpeechTiming, approximatePhoneme };
