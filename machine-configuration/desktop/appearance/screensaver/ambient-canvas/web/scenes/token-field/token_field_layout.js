window.AmbientCanvasTokenFieldLayout = (function buildTokenFieldLayoutModule() {
  const NOISE_PROBABILITY_UNDER_WORD = 0.45;
  const NOISE_PROBABILITY_IN_GAP = 0.1;
  const LARGEST_GAP_CELLS = 9;
  const SMALLEST_WORD_BRIGHTNESS = 0.62;
  const WORD_ORDER_JITTER = 0.06;
  const CHARACTER_ORDER_STAGGER = 0.03;
  const GAP_ORDER_JITTER = 0.08;
  const BROAD_LOBE_DEPTH = 0.1;
  const FINE_LOBE_DEPTH = 0.06;
  const LARGEST_RAW_ORDER =
    1 +
    BROAD_LOBE_DEPTH +
    FINE_LOBE_DEPTH +
    WORD_ORDER_JITTER +
    GAP_ORDER_JITTER;
  const EMPTY_GLYPH = -1;

  function createRandomStream(seed) {
    let streamState = seed | 0;
    return function nextRandomFraction() {
      streamState = (streamState + 0x6d2b79f5) | 0;
      let mixed = Math.imul(
        streamState ^ (streamState >>> 15),
        1 | streamState,
      );
      mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed);
      return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
    };
  }

  function resolveGlyphAlphabet(vocabulary) {
    const characters = new Set(vocabulary.operatorNoiseCharacters);
    for (const pool of vocabulary.tokenPools) {
      for (const token of pool.tokens) {
        for (const character of token) {
          if (character !== " ") characters.add(character);
        }
      }
    }
    return Array.from(characters).sort();
  }

  function pickWeightedPool(pools, randomFraction) {
    const totalWeight = pools.reduce((sum, pool) => sum + pool.weight, 0);
    let remaining = randomFraction * totalWeight;
    for (const pool of pools) {
      remaining -= pool.weight;
      if (remaining < 0) return pool;
    }
    return pools[pools.length - 1];
  }

  function pickFrom(items, randomFraction) {
    return items[Math.floor(randomFraction * items.length)];
  }

  function resolveShapedRadius(column, row, grid, lobes) {
    const horizontal = ((column + 0.5) / grid.columnCount) * 2 - 1;
    const vertical = ((row + 0.5) / grid.rowCount) * 2 - 1;
    const radius = Math.hypot(horizontal, vertical) / Math.SQRT2;
    const angle = Math.atan2(vertical, horizontal);
    const lobeOffset =
      BROAD_LOBE_DEPTH * Math.sin(2 * angle + lobes.broadPhase) +
      FINE_LOBE_DEPTH * Math.sin(5 * angle + lobes.finePhase);
    return radius * (1 + lobeOffset);
  }

  function normalizedOrder(rawOrder) {
    return Math.min(1, Math.max(0, rawOrder / LARGEST_RAW_ORDER));
  }

  function createEmptyGeneration(grid, random) {
    const cellCount = grid.columnCount * grid.rowCount;
    const generation = {
      wordGlyphIndices: new Int16Array(cellCount).fill(EMPTY_GLYPH),
      wordColourIndices: new Uint8Array(cellCount),
      wordBrightness: new Float32Array(cellCount),
      noiseGlyphIndices: new Int16Array(cellCount).fill(EMPTY_GLYPH),
      clearingOrder: new Float32Array(cellCount),
    };
    const lobes = {
      broadPhase: random() * Math.PI * 2,
      finePhase: random() * Math.PI * 2,
    };
    for (let row = 0; row < grid.rowCount; row += 1) {
      for (let column = 0; column < grid.columnCount; column += 1) {
        generation.clearingOrder[row * grid.columnCount + column] =
          normalizedOrder(
            resolveShapedRadius(column, row, grid, lobes) +
              random() * GAP_ORDER_JITTER,
          );
      }
    }
    generation.lobes = lobes;
    return generation;
  }

  function placeToken(generation, grid, glyphs, placement) {
    const { token, colourIndex, brightness, row, startColumn, wordJitter } =
      placement;
    for (let offset = 0; offset < token.length; offset += 1) {
      const column = startColumn + offset;
      if (column >= grid.columnCount) return;
      if (token[offset] === " ") continue;
      const cellIndex = row * grid.columnCount + column;
      generation.wordGlyphIndices[cellIndex] = glyphs.indexOf(token[offset]);
      generation.wordColourIndices[cellIndex] = colourIndex;
      generation.wordBrightness[cellIndex] = brightness;
      generation.clearingOrder[cellIndex] = normalizedOrder(
        resolveShapedRadius(column, row, grid, generation.lobes) +
          wordJitter +
          (offset / token.length) * CHARACTER_ORDER_STAGGER,
      );
    }
  }

  function placeRowTokens(generation, grid, vocabulary, glyphs, row, random) {
    let column = Math.floor(random() * 4);
    while (column < grid.columnCount) {
      const pool = pickWeightedPool(vocabulary.tokenPools, random());
      const token = pickFrom(pool.tokens, random());
      placeToken(generation, grid, glyphs, {
        token,
        colourIndex: vocabulary.syntaxClasses.indexOf(pool.syntaxClass),
        brightness:
          SMALLEST_WORD_BRIGHTNESS + random() * (1 - SMALLEST_WORD_BRIGHTNESS),
        row,
        startColumn: column,
        wordJitter: random() * WORD_ORDER_JITTER,
      });
      const gapReach = random() < 0.25 ? LARGEST_GAP_CELLS : 3;
      column += token.length + 1 + Math.floor(random() * gapReach);
    }
  }

  function scatterOperatorNoise(generation, vocabulary, glyphs, random) {
    const noiseCount = vocabulary.operatorNoiseCharacters.length;
    for (
      let index = 0;
      index < generation.noiseGlyphIndices.length;
      index += 1
    ) {
      const carriesWord = generation.wordGlyphIndices[index] !== EMPTY_GLYPH;
      const probability = carriesWord
        ? NOISE_PROBABILITY_UNDER_WORD
        : NOISE_PROBABILITY_IN_GAP;
      const appears = random() < probability;
      const character = vocabulary.operatorNoiseCharacters.charAt(
        Math.floor(random() * noiseCount),
      );
      if (appears) {
        generation.noiseGlyphIndices[index] = glyphs.indexOf(character);
      }
    }
  }

  function buildTokenFieldLayout(grid, generationCount, vocabulary) {
    const glyphs = resolveGlyphAlphabet(vocabulary);
    const generations = [];
    for (let index = 0; index < generationCount; index += 1) {
      const random = createRandomStream(0x51ed270b + index * 0x9e3779b1);
      const generation = createEmptyGeneration(grid, random);
      for (let row = 0; row < grid.rowCount; row += 1) {
        placeRowTokens(generation, grid, vocabulary, glyphs, row, random);
      }
      scatterOperatorNoise(generation, vocabulary, glyphs, random);
      generations.push(generation);
    }
    return { glyphs, generations };
  }

  return { EMPTY_GLYPH, resolveGlyphAlphabet, buildTokenFieldLayout };
})();
