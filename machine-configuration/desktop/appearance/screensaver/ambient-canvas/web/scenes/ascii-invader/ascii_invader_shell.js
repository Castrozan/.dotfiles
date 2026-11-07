const INVADER_SPRITE_ROWS = [
  "..#.....#..",
  "...#...#...",
  "..#######..",
  ".##.###.##.",
  "###########",
  "#.#######.#",
  "#.#.....#.#",
  "...##.##...",
];
const INVADER_SPRITE_HEIGHT = INVADER_SPRITE_ROWS.length;
const INVADER_SPRITE_WIDTH = INVADER_SPRITE_ROWS[0].length;
const SHELL_LONGITUDE_SPAN = 2.35;
const SHELL_LATITUDE_SPAN = 1.15;
const SHELL_RADIUS = 1.0;
const GLYPHS_PER_SPRITE_PIXEL = 6;
const GLYPH_ALPHABET = "@#*+=-%:";
const PHOSPHOR_PALETTE = [
  [1.0, 0.24, 0.28],
  [0.28, 1.0, 0.42],
  [0.34, 0.52, 1.0],
  [0.26, 0.94, 0.96],
  [1.0, 0.36, 0.9],
  [1.0, 0.88, 0.3],
  [1.0, 1.0, 1.0],
];

function hashedUnitInterval(index, salt) {
  const mixed = Math.sin(index * 127.1 + salt * 311.7) * 43758.5453;
  return mixed - Math.floor(mixed);
}

function listLitColumnIndices(spriteRow) {
  const litColumnIndices = [];
  for (
    let columnIndex = 0;
    columnIndex < INVADER_SPRITE_WIDTH;
    columnIndex += 1
  ) {
    if (spriteRow[columnIndex] === "#") {
      litColumnIndices.push(columnIndex);
    }
  }
  return litColumnIndices;
}

function listLitSpritePixels() {
  return INVADER_SPRITE_ROWS.flatMap((spriteRow, rowIndex) =>
    listLitColumnIndices(spriteRow).map((columnIndex) => ({
      rowIndex,
      columnIndex,
    })),
  );
}

function buildShellPoint(pointIndex, rowIndex, columnIndex) {
  const acrossSprite =
    (columnIndex + hashedUnitInterval(pointIndex, 53.0)) /
      INVADER_SPRITE_WIDTH -
    0.5;
  const downSprite =
    (rowIndex + hashedUnitInterval(pointIndex, 59.0)) / INVADER_SPRITE_HEIGHT -
    0.5;
  const longitude = acrossSprite * SHELL_LONGITUDE_SPAN;
  const latitude = downSprite * SHELL_LATITUDE_SPAN;
  return {
    restingPosition: [
      SHELL_RADIUS * Math.cos(latitude) * Math.sin(longitude),
      SHELL_RADIUS * Math.sin(latitude),
      SHELL_RADIUS * Math.cos(latitude) * Math.cos(longitude),
    ],
    glyph: GLYPH_ALPHABET.charAt(
      Math.floor(hashedUnitInterval(pointIndex, 3.0) * GLYPH_ALPHABET.length),
    ),
    colour:
      PHOSPHOR_PALETTE[
        Math.floor(
          hashedUnitInterval(pointIndex, 7.0) * PHOSPHOR_PALETTE.length,
        )
      ],
    flickerPhase: hashedUnitInterval(pointIndex, 11.0) * Math.PI * 2.0,
  };
}

function buildShellPoints() {
  const points = [];
  for (const { rowIndex, columnIndex } of listLitSpritePixels()) {
    for (
      let clusterIndex = 0;
      clusterIndex < GLYPHS_PER_SPRITE_PIXEL;
      clusterIndex += 1
    ) {
      points.push(buildShellPoint(points.length, rowIndex, columnIndex));
    }
  }
  return points;
}

function tumbledPosition(restingPosition, elapsedSeconds) {
  const yawAngle = elapsedSeconds * 0.62;
  const pitchAngle = Math.sin(elapsedSeconds * 0.23) * 0.85;
  const rollAngle = elapsedSeconds * 0.17;
  const [restingX, restingY, restingZ] = restingPosition;

  const rolledX =
    restingX * Math.cos(rollAngle) - restingY * Math.sin(rollAngle);
  const rolledY =
    restingX * Math.sin(rollAngle) + restingY * Math.cos(rollAngle);

  const yawedX = rolledX * Math.cos(yawAngle) + restingZ * Math.sin(yawAngle);
  const yawedZ = -rolledX * Math.sin(yawAngle) + restingZ * Math.cos(yawAngle);

  const pitchedY =
    rolledY * Math.cos(pitchAngle) - yawedZ * Math.sin(pitchAngle);
  const pitchedZ =
    rolledY * Math.sin(pitchAngle) + yawedZ * Math.cos(pitchAngle);

  return [yawedX, pitchedY, pitchedZ];
}

window.AmbientCanvasAsciiInvaderShell = (function buildAsciiInvaderShell() {
  return {
    buildShellPoints,
    tumbledPosition,
    hashedUnitInterval,
    PHOSPHOR_PALETTE,
    GLYPH_ALPHABET,
  };
})();
