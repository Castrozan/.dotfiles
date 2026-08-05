window.AmbientCanvasAsciiInvaderShell = (function buildAsciiInvaderShell() {
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

  function buildShellPoints() {
    const points = [];
    const spriteHeight = INVADER_SPRITE_ROWS.length;
    const spriteWidth = INVADER_SPRITE_ROWS[0].length;
    for (let rowIndex = 0; rowIndex < spriteHeight; rowIndex += 1) {
      for (let columnIndex = 0; columnIndex < spriteWidth; columnIndex += 1) {
        if (INVADER_SPRITE_ROWS[rowIndex][columnIndex] !== "#") {
          continue;
        }
        for (
          let clusterIndex = 0;
          clusterIndex < GLYPHS_PER_SPRITE_PIXEL;
          clusterIndex += 1
        ) {
          const index = points.length;
          const acrossSprite =
            (columnIndex + hashedUnitInterval(index, 53.0)) / spriteWidth - 0.5;
          const downSprite =
            (rowIndex + hashedUnitInterval(index, 59.0)) / spriteHeight - 0.5;
          const longitude = acrossSprite * SHELL_LONGITUDE_SPAN;
          const latitude = downSprite * SHELL_LATITUDE_SPAN;
          points.push({
            restingPosition: [
              SHELL_RADIUS * Math.cos(latitude) * Math.sin(longitude),
              SHELL_RADIUS * Math.sin(latitude),
              SHELL_RADIUS * Math.cos(latitude) * Math.cos(longitude),
            ],
            glyph: GLYPH_ALPHABET.charAt(
              Math.floor(
                hashedUnitInterval(index, 3.0) * GLYPH_ALPHABET.length,
              ),
            ),
            colour:
              PHOSPHOR_PALETTE[
                Math.floor(
                  hashedUnitInterval(index, 7.0) * PHOSPHOR_PALETTE.length,
                )
              ],
            flickerPhase: hashedUnitInterval(index, 11.0) * Math.PI * 2.0,
          });
        }
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
    const yawedZ =
      -rolledX * Math.sin(yawAngle) + restingZ * Math.cos(yawAngle);

    const pitchedY =
      rolledY * Math.cos(pitchAngle) - yawedZ * Math.sin(pitchAngle);
    const pitchedZ =
      rolledY * Math.sin(pitchAngle) + yawedZ * Math.cos(pitchAngle);

    return [yawedX, pitchedY, pitchedZ];
  }

  return {
    buildShellPoints,
    tumbledPosition,
    hashedUnitInterval,
    PHOSPHOR_PALETTE,
    GLYPH_ALPHABET,
  };
})();
