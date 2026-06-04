local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

local figureSpace = "\u{2007}"
local occupiedWorkspaceColor = { list = "System", name = "controlAccentColor" }
local unoccupiedWorkspaceColor = { list = "System", name = "labelColor" }

local function paddedNumberText(workspaceNumber)
  if workspaceNumber < 10 then
    return figureSpace .. workspaceNumber
  end
  return tostring(workspaceNumber)
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
    local numberText = paddedNumberText(workspaceNumber)
    local cellText
    if workspaceNumber == currentWorkspaceNumber then
      cellText = "[" .. numberText .. "]"
    else
      cellText = figureSpace .. numberText .. figureSpace
    end
    local cellColor = occupiedWorkspaceNumbers[workspaceNumber] and occupiedWorkspaceColor or unoccupiedWorkspaceColor
    styledTitle = styledTitle .. hs.styledtext.new(cellText, { color = cellColor })
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
