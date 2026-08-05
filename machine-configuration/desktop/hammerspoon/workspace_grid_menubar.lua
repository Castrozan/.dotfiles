local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

local menuBarFont = { name = "Menlo", size = 13 }
local accentColor = { list = "System", name = "controlAccentColor" }
local labelColor = { list = "System", name = "labelColor" }

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

local function cellText(cell)
	local paddedNumber = string.format("%02d", cell.workspaceNumber)
	if cell.isActive then
		return "[" .. paddedNumber .. "]"
	end
	return paddedNumber
end

local function cellAttributes(cell)
	if cell.isActive or cell.isOccupied then
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
	for cellIndex, cell in ipairs(cells) do
		if cellIndex > 1 then
			styledTitle = styledTitle .. hs.styledtext.new(" ", { font = menuBarFont })
		end
		styledTitle = styledTitle .. hs.styledtext.new(cellText(cell), cellAttributes(cell))
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
