-- Owns the menu-bar workspace indicator: renders only the active row's seven
-- workspaces, e.g. "15 16 17 [18] 19 20 21" on the third row, with the active
-- workspace bracketed. Numbers are space-padded to two digits and drawn in a
-- monospaced font so the indicator keeps a constant width on every row.
-- Workspaces that hold a window are drawn bright; empty ones are dimmed.

local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

local menuBarFont = { name = "Menlo", size = 14 }
local occupiedWorkspaceColor = { white = 1.0, alpha = 1.0 }
local emptyWorkspaceColor = { white = 1.0, alpha = 0.35 }

function workspaceGridMenuBar.render(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  if not menuBarIndicatorHandle then
    return
  end
  occupiedWorkspaceNumbers = occupiedWorkspaceNumbers or {}
  local rowIndex = math.floor((currentWorkspaceNumber - 1) / columnsPerRow)
  local firstWorkspaceInRow = rowIndex * columnsPerRow + 1
  local lastWorkspaceInRow = firstWorkspaceInRow + columnsPerRow - 1
  local title = ""
  local colorRanges = {}
  for workspaceNumber = firstWorkspaceInRow, lastWorkspaceInRow do
    local numberText = string.format("%2d", workspaceNumber)
    local cellText
    if workspaceNumber == currentWorkspaceNumber then
      cellText = "[" .. numberText .. "]"
    else
      cellText = " " .. numberText .. " "
    end
    local cellStartIndex = #title + 1
    title = title .. cellText
    table.insert(colorRanges, {
      startIndex = cellStartIndex,
      endIndex = #title,
      color = occupiedWorkspaceNumbers[workspaceNumber] and occupiedWorkspaceColor or emptyWorkspaceColor,
    })
  end
  local styledTitle = hs.styledtext.new(title, { font = menuBarFont })
  for _, range in ipairs(colorRanges) do
    styledTitle = styledTitle:setStyle({ color = range.color }, range.startIndex, range.endIndex)
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
