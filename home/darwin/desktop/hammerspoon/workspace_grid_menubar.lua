local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

local figureSpace = "\u{2007}"
local accentColor = { list = "System", name = "controlAccentColor" }
local labelColor = { list = "System", name = "labelColor" }
local activeTextColor = { list = "System", name = "selectedMenuItemTextColor" }

local function cellAttributes(isActive, isOccupied)
  if isActive then
    return { color = activeTextColor, backgroundColor = accentColor }
  end
  if isOccupied then
    return { color = accentColor }
  end
  return { color = labelColor }
end

function workspaceGridMenuBar.render(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  if not menuBarIndicatorHandle then
    return
  end
  occupiedWorkspaceNumbers = occupiedWorkspaceNumbers or {}
  local rowIndex = math.floor((currentWorkspaceNumber - 1) / columnsPerRow)
  local firstWorkspaceInRow = rowIndex * columnsPerRow + 1
  local lastWorkspaceInRow = firstWorkspaceInRow + columnsPerRow - 1
  local styledTitle = hs.styledtext.new("")
  for workspaceNumber = firstWorkspaceInRow, lastWorkspaceInRow do
    local cellText = figureSpace .. workspaceNumber .. figureSpace
    local attributes = cellAttributes(
      workspaceNumber == currentWorkspaceNumber,
      occupiedWorkspaceNumbers[workspaceNumber] == true
    )
    styledTitle = styledTitle .. hs.styledtext.new(cellText, attributes)
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
