local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

local menuBarFont = { name = "Menlo", size = 13 }
local cellCharacterWidth = 3
local accentColor = { list = "System", name = "controlAccentColor" }
local labelColor = { list = "System", name = "labelColor" }
local activeTextColor = { list = "System", name = "selectedMenuItemTextColor" }

function workspaceGridMenuBar.cellsForRow(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  occupiedWorkspaceNumbers = occupiedWorkspaceNumbers or {}
  local rowIndex = math.floor((currentWorkspaceNumber - 1) / columnsPerRow)
  local firstWorkspaceInRow = rowIndex * columnsPerRow + 1
  local cells = {}
  for slotIndex = 0, columnsPerRow - 1 do
    local workspaceNumber = firstWorkspaceInRow + slotIndex
    table.insert(cells, {
      workspaceNumber = workspaceNumber,
      isActive = workspaceNumber == currentWorkspaceNumber,
      isOccupied = occupiedWorkspaceNumbers[workspaceNumber] == true,
    })
  end
  return cells
end

local function centeredText(value, width)
  local text = tostring(value)
  local totalPadding = width - #text
  if totalPadding <= 0 then
    return text
  end
  local leftPadding = math.floor(totalPadding / 2)
  return string.rep(" ", leftPadding) .. text .. string.rep(" ", totalPadding - leftPadding)
end

local function cellAttributes(cell)
  if cell.isActive then
    return { font = menuBarFont, color = activeTextColor, backgroundColor = accentColor }
  end
  if cell.isOccupied then
    return { font = menuBarFont, color = accentColor }
  end
  return { font = menuBarFont, color = labelColor }
end

function workspaceGridMenuBar.render(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  if not menuBarIndicatorHandle then
    return
  end
  local cells = workspaceGridMenuBar.cellsForRow(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  local styledTitle = hs.styledtext.new("")
  for _, cell in ipairs(cells) do
    local cellText = centeredText(cell.workspaceNumber, cellCharacterWidth)
    styledTitle = styledTitle .. hs.styledtext.new(cellText, cellAttributes(cell))
  end
  menuBarIndicatorHandle:setTitle(styledTitle)
end

function workspaceGridMenuBar.deleteIndicator()
  if menuBarIndicatorHandle then
    menuBarIndicatorHandle:delete()
    menuBarIndicatorHandle = nil
  end
end

return workspaceGridMenuBar
