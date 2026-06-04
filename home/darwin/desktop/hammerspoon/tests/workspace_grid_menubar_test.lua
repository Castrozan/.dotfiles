local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local createdMenuBars = {}
hs = {
  menubar = {
    new = function()
      local menuBarItem = { deleted = false, icon = nil }
      function menuBarItem:setIcon(image) self.icon = image end
      function menuBarItem:delete() self.deleted = true end
      table.insert(createdMenuBars, menuBarItem)
      return menuBarItem
    end,
  },
  canvas = {
    new = function()
      local canvas = {}
      function canvas:replaceElements(elements) self.elements = elements end
      function canvas:imageFromCanvas() return { isImage = true } end
      function canvas:delete() end
      return canvas
    end,
  },
}

local function liveMenuBarCount()
  local count = 0
  for _, menuBarItem in ipairs(createdMenuBars) do
    if not menuBarItem.deleted then count = count + 1 end
  end
  return count
end

local menuBar = require("workspace_grid_menubar")

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
  if expectedValue ~= actualValue then
    failureCount = failureCount + 1
    print(string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue)))
  else
    print(string.format("PASS: %s", description))
  end
end

local function workspaceNumbers(cells)
  local numbers = {}
  for _, cell in ipairs(cells) do
    table.insert(numbers, cell.workspaceNumber)
  end
  return table.concat(numbers, " ")
end

local function findCell(cells, workspaceNumber)
  for _, cell in ipairs(cells) do
    if cell.workspaceNumber == workspaceNumber then
      return cell
    end
  end
  return nil
end

local firstRowCells = menuBar.cellsForRow(2, 7, { [2] = true, [5] = true })
expectEqual("the active row shows exactly seven workspaces", 7, #firstRowCells)
expectEqual("the first row holds workspaces one through seven", "1 2 3 4 5 6 7", workspaceNumbers(firstRowCells))
expectEqual("the current workspace is marked active", true, findCell(firstRowCells, 2).isActive)
expectEqual("a workspace with a window is marked occupied", true, findCell(firstRowCells, 5).isOccupied)
expectEqual("an empty workspace is not marked occupied", false, findCell(firstRowCells, 3).isOccupied)
expectEqual("a non-current workspace is not marked active", false, findCell(firstRowCells, 5).isActive)

local thirdRowCells = menuBar.cellsForRow(18, 7, { [18] = true })
expectEqual("the third row holds its own seven workspaces", "15 16 17 18 19 20 21", workspaceNumbers(thirdRowCells))
expectEqual("the third row marks its current workspace active", true, findCell(thirdRowCells, 18).isActive)
expectEqual("the third row always has seven slots like every other row", #firstRowCells, #thirdRowCells)

menuBar.render(2, 7, { [2] = true })
expectEqual("first load shows exactly one indicator", 1, liveMenuBarCount())
expectEqual("rendering sets a menu-bar icon", true, createdMenuBars[1].icon.isImage)

local function simulateReload()
  menuBar.deleteIndicator()
  package.loaded["workspace_grid_menubar"] = nil
  menuBar = require("workspace_grid_menubar")
end

simulateReload()
menuBar.render(1, 7)
expectEqual("a reload leaves exactly one indicator, no orphan frozen at the old workspace", 1, liveMenuBarCount())

os.exit(failureCount == 0 and 0 or 1)
