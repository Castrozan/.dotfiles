const bonsaiWoodColorHex = "#b5844a";
const bonsaiLeafColorPalette = ["#4fbf5f", "#5fcf6f", "#6fdf7f", "#7fe88f"];

function bonsaiIsInsideGrid(state, columnIndex, rowIndex) {
  return (
    columnIndex >= 0 &&
    columnIndex < state.columnCount &&
    rowIndex >= 0 &&
    rowIndex < state.rowCount
  );
}
function bonsaiPushCell(state, columnIndex, rowIndex, glyph, colorHex) {
  if (bonsaiIsInsideGrid(state, columnIndex, rowIndex)) {
    state.orderedCells.push({ columnIndex, rowIndex, glyph, colorHex });
  }
}
function bonsaiRandomLeafColorHex() {
  const paletteIndex = Math.floor(
    Math.random() * bonsaiLeafColorPalette.length,
  );
  return bonsaiLeafColorPalette[paletteIndex];
}
function bonsaiChooseWoodGlyph(columnDelta, rowDelta) {
  if (rowDelta === 0) return "~";
  if (columnDelta < 0) return "\\";
  if (columnDelta > 0) return "/";
  return "|";
}
function bonsaiChooseGrowthDelta(branchType, remainingLife) {
  const columnDelta = Math.floor(Math.random() * 3) - 1;
  return bonsaiResolveBranchGrowthDelta(branchType, remainingLife, columnDelta);
}
function bonsaiResolveBranchGrowthDelta(
  branchType,
  remainingLife,
  columnDelta,
) {
  if (branchType === "trunk") {
    return bonsaiResolveTrunkGrowthDelta(columnDelta, remainingLife);
  }
  if (branchType === "shootLeft") return bonsaiResolveLeftShootGrowthDelta();
  if (branchType === "shootRight") return bonsaiResolveRightShootGrowthDelta();
  return bonsaiResolveDefaultGrowthDelta(columnDelta);
}
function bonsaiResolveTrunkGrowthDelta(columnDelta, remainingLife) {
  let rowDelta = 0;
  if (remainingLife > 3) rowDelta = Math.random() < 0.7 ? -1 : 0;
  return { columnDelta, rowDelta };
}
function bonsaiResolveLeftShootGrowthDelta() {
  const columnDelta = Math.random() < 0.7 ? -1 : 0;
  const rowDelta = Math.random() < 0.5 ? -1 : 0;
  return { columnDelta, rowDelta };
}
function bonsaiResolveRightShootGrowthDelta() {
  const columnDelta = Math.random() < 0.7 ? 1 : 0;
  const rowDelta = Math.random() < 0.5 ? -1 : 0;
  return { columnDelta, rowDelta };
}
function bonsaiResolveDefaultGrowthDelta(columnDelta) {
  const rowDelta = Math.random() < 0.3 ? -1 : 0;
  return { columnDelta, rowDelta };
}
function bonsaiAppendLeafCluster(state, centerColumn, centerRow) {
  const clusterSize = 3 + Math.floor(Math.random() * 4);
  for (let leafIndex = 0; leafIndex < clusterSize; leafIndex += 1) {
    const columnIndex = centerColumn + Math.floor(Math.random() * 3) - 1;
    const rowIndex = centerRow + Math.floor(Math.random() * 3) - 1;
    const glyph = Math.random() < 0.5 ? "&" : "*";
    bonsaiPushCell(
      state,
      columnIndex,
      rowIndex,
      glyph,
      bonsaiRandomLeafColorHex(),
    );
  }
}
function bonsaiGrowBranch(
  state,
  startColumn,
  startRow,
  branchType,
  initialLife,
) {
  let columnIndex = startColumn;
  let rowIndex = startRow;
  let remainingLife = initialLife;
  while (remainingLife > 0) {
    remainingLife -= 1;
    const delta = bonsaiChooseGrowthDelta(branchType, remainingLife);
    bonsaiGrowShootIfReady(
      state,
      columnIndex,
      rowIndex,
      branchType,
      remainingLife,
    );
    columnIndex = columnIndex + delta.columnDelta;
    rowIndex = rowIndex + delta.rowDelta;
    if (!bonsaiIsInsideGrid(state, columnIndex, rowIndex)) break;
    bonsaiAppendBranchCell(state, columnIndex, rowIndex, remainingLife, delta);
  }
}
function bonsaiGrowShootIfReady(
  state,
  columnIndex,
  rowIndex,
  branchType,
  remainingLife,
) {
  const canSpawnShoot = branchType === "trunk" && remainingLife > 4;
  if (!canSpawnShoot || Math.random() >= 0.14) return;
  const shootType = Math.random() < 0.5 ? "shootLeft" : "shootRight";
  const shootLife = Math.floor(remainingLife * 0.5) + 2;
  bonsaiGrowBranch(state, columnIndex, rowIndex, shootType, shootLife);
}
function bonsaiAppendBranchCell(
  state,
  columnIndex,
  rowIndex,
  remainingLife,
  delta,
) {
  if (remainingLife < 3) {
    bonsaiAppendLeafCluster(state, columnIndex, rowIndex);
    return;
  }
  const glyph = bonsaiChooseWoodGlyph(delta.columnDelta, delta.rowDelta);
  bonsaiPushCell(state, columnIndex, rowIndex, glyph, bonsaiWoodColorHex);
}
