local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

local menuBarHeight = 22
local cellWidth = 22
local pillHorizontalInset = 2
local pillVerticalInset = 3
local pillCornerRadius = 5
local textSize = 13
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

local function indicatorImage(cells)
  local indicatorWidth = #cells * cellWidth
  local canvas = hs.canvas.new({ x = 0, y = 0, w = indicatorWidth, h = menuBarHeight })
  local elements = {}
  for slotIndex, cell in ipairs(cells) do
    local cellLeft = (slotIndex - 1) * cellWidth
    if cell.isActive then
      table.insert(elements, {
        type = "rectangle",
        action = "fill",
        fillColor = accentColor,
        roundedRectRadii = { xRadius = pillCornerRadius, yRadius = pillCornerRadius },
        frame = {
          x = cellLeft + pillHorizontalInset,
          y = pillVerticalInset,
          w = cellWidth - pillHorizontalInset * 2,
          h = menuBarHeight - pillVerticalInset * 2,
        },
      })
    end
    local cellTextColor = labelColor
    if cell.isActive then
      cellTextColor = activeTextColor
    elseif cell.isOccupied then
      cellTextColor = accentColor
    end
    table.insert(elements, {
      type = "text",
      text = tostring(cell.workspaceNumber),
      textColor = cellTextColor,
      textSize = textSize,
      textAlignment = "center",
      frame = { x = cellLeft, y = 2, w = cellWidth, h = menuBarHeight },
    })
  end
  canvas:replaceElements(elements)
  local image = canvas:imageFromCanvas()
  canvas:delete()
  return image
end

function workspaceGridMenuBar.render(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  if not menuBarIndicatorHandle then
    return
  end
  local cells = workspaceGridMenuBar.cellsForRow(currentWorkspaceNumber, columnsPerRow, occupiedWorkspaceNumbers)
  menuBarIndicatorHandle:setIcon(indicatorImage(cells), false)
end

function workspaceGridMenuBar.deleteIndicator()
  if menuBarIndicatorHandle then
    menuBarIndicatorHandle:delete()
    menuBarIndicatorHandle = nil
  end
end

return workspaceGridMenuBar
