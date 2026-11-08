const tokenFieldNoiseProbabilityUnderWord = 0.45;
const tokenFieldNoiseProbabilityInGap = 0.1;
const tokenFieldLargestGapCells = 9;
const tokenFieldSmallestWordBrightness = 0.62;
const tokenFieldWordOrderJitter = 0.06;
const tokenFieldCharacterOrderStagger = 0.03;
const tokenFieldGapOrderJitter = 0.08;
const tokenFieldBroadLobeDepth = 0.1;
const tokenFieldFineLobeDepth = 0.06;
const tokenFieldLargestRawOrder =
  1 +
  tokenFieldBroadLobeDepth +
  tokenFieldFineLobeDepth +
  tokenFieldWordOrderJitter +
  tokenFieldGapOrderJitter;
const tokenFieldEmptyGlyph = -1;

function tokenFieldCreateRandomStream(seed) {
  let streamState = seed | 0;
  return function nextRandomFraction() {
    streamState = (streamState + 0x6d2b79f5) | 0;
    let mixed = Math.imul(streamState ^ (streamState >>> 15), 1 | streamState);
    mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed);
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
  };
}

function tokenFieldResolveGlyphAlphabet(vocabulary) {
  const characters = new Set(vocabulary.operatorNoiseCharacters);
  for (const pool of vocabulary.tokenPools) {
    for (const character of pool.tokens.join("")) {
      if (character !== " ") characters.add(character);
    }
  }
  return Array.from(characters).sort();
}

function tokenFieldPickWeightedPool(pools, randomFraction) {
  const totalWeight = pools.reduce((sum, pool) => sum + pool.weight, 0);
  let remaining = randomFraction * totalWeight;
  for (const pool of pools) {
    remaining -= pool.weight;
    if (remaining < 0) return pool;
  }
  return pools[pools.length - 1];
}

function tokenFieldPickFrom(items, randomFraction) {
  return items[Math.floor(randomFraction * items.length)];
}

function tokenFieldResolveShapedRadius(column, row, grid, lobes) {
  const horizontal = ((column + 0.5) / grid.columnCount) * 2 - 1;
  const vertical = ((row + 0.5) / grid.rowCount) * 2 - 1;
  const radius = Math.hypot(horizontal, vertical) / Math.SQRT2;
  const angle = Math.atan2(vertical, horizontal);
  const lobeOffset =
    tokenFieldBroadLobeDepth * Math.sin(2 * angle + lobes.broadPhase) +
    tokenFieldFineLobeDepth * Math.sin(5 * angle + lobes.finePhase);
  return radius * (1 + lobeOffset);
}

function tokenFieldNormalizedOrder(rawOrder) {
  return Math.min(1, Math.max(0, rawOrder / tokenFieldLargestRawOrder));
}

function tokenFieldCreateEmptyGeneration(grid, random) {
  const cellCount = grid.columnCount * grid.rowCount;
  const generation = {
    wordGlyphIndices: new Int16Array(cellCount).fill(tokenFieldEmptyGlyph),
    wordColourIndices: new Uint8Array(cellCount),
    wordBrightness: new Float32Array(cellCount),
    noiseGlyphIndices: new Int16Array(cellCount).fill(tokenFieldEmptyGlyph),
    clearingOrder: new Float32Array(cellCount),
    lobes: {
      broadPhase: random() * Math.PI * 2,
      finePhase: random() * Math.PI * 2,
    },
  };
  for (let cellIndex = 0; cellIndex < cellCount; cellIndex += 1) {
    generation.clearingOrder[cellIndex] = tokenFieldNormalizedOrder(
      tokenFieldResolveShapedRadius(
        cellIndex % grid.columnCount,
        Math.floor(cellIndex / grid.columnCount),
        grid,
        generation.lobes,
      ) +
        random() * tokenFieldGapOrderJitter,
    );
  }
  return generation;
}

function tokenFieldPlaceToken(field, placement) {
  const { generation, grid, glyphs } = field;
  const { token, colourIndex, brightness, row, startColumn, wordJitter } =
    placement;
  const visibleLength = Math.min(token.length, grid.columnCount - startColumn);
  for (let offset = 0; offset < visibleLength; offset += 1) {
    if (token[offset] === " ") continue;
    const column = startColumn + offset;
    const cellIndex = row * grid.columnCount + column;
    generation.wordGlyphIndices[cellIndex] = glyphs.indexOf(token[offset]);
    generation.wordColourIndices[cellIndex] = colourIndex;
    generation.wordBrightness[cellIndex] = brightness;
    generation.clearingOrder[cellIndex] = tokenFieldNormalizedOrder(
      tokenFieldResolveShapedRadius(column, row, grid, generation.lobes) +
        wordJitter +
        (offset / token.length) * tokenFieldCharacterOrderStagger,
    );
  }
}

function tokenFieldPlaceRowTokens(field, row) {
  const { grid, vocabulary, random } = field;
  let column = Math.floor(random() * 4);
  while (column < grid.columnCount) {
    const pool = tokenFieldPickWeightedPool(vocabulary.tokenPools, random());
    const token = tokenFieldPickFrom(pool.tokens, random());
    tokenFieldPlaceToken(field, {
      token,
      colourIndex: vocabulary.syntaxClasses.indexOf(pool.syntaxClass),
      brightness:
        tokenFieldSmallestWordBrightness +
        random() * (1 - tokenFieldSmallestWordBrightness),
      row,
      startColumn: column,
      wordJitter: random() * tokenFieldWordOrderJitter,
    });
    const gapReach = random() < 0.25 ? tokenFieldLargestGapCells : 3;
    column += token.length + 1 + Math.floor(random() * gapReach);
  }
}

function tokenFieldScatterOperatorNoise(field) {
  const { generation, vocabulary, glyphs, random } = field;
  const noiseCharacters = vocabulary.operatorNoiseCharacters;
  for (let index = 0; index < generation.noiseGlyphIndices.length; index += 1) {
    const probability =
      generation.wordGlyphIndices[index] === tokenFieldEmptyGlyph
        ? tokenFieldNoiseProbabilityInGap
        : tokenFieldNoiseProbabilityUnderWord;
    const appears = random() < probability;
    const character = noiseCharacters.charAt(
      Math.floor(random() * noiseCharacters.length),
    );
    if (appears) {
      generation.noiseGlyphIndices[index] = glyphs.indexOf(character);
    }
  }
}

function tokenFieldBuildGeneration(grid, vocabulary, glyphs, generationIndex) {
  const random = tokenFieldCreateRandomStream(
    0x51ed270b + generationIndex * 0x9e3779b1,
  );
  const generation = tokenFieldCreateEmptyGeneration(grid, random);
  const field = { generation, grid, vocabulary, glyphs, random };
  for (let row = 0; row < grid.rowCount; row += 1) {
    tokenFieldPlaceRowTokens(field, row);
  }
  tokenFieldScatterOperatorNoise(field);
  return generation;
}

function tokenFieldBuildLayout(grid, generationCount, vocabulary) {
  const glyphs = tokenFieldResolveGlyphAlphabet(vocabulary);
  const generations = Array.from({ length: generationCount }, (_, index) =>
    tokenFieldBuildGeneration(grid, vocabulary, glyphs, index),
  );
  return { glyphs, generations };
}

window.AmbientCanvasTokenFieldLayout = {
  EMPTY_GLYPH: tokenFieldEmptyGlyph,
  buildTokenFieldLayout: tokenFieldBuildLayout,
};
