local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local styledTextMeta = {}
styledTextMeta.__concat = function(left, right)
  local segments = {}
  for _, segment in ipairs(left.segments) do
    table.insert(segments, segment)
  end
  for _, segment in ipairs(right.segments) do
    table.insert(segments, segment)
  end
  return setmetatable({ segments = segments }, styledTextMeta)
end

local createdMenuBars = {}
hs = {
  menubar = {
    new = function()
      local menuBarItem = { deleted = false, title = nil }
      function menuBarItem:setTitle(newTitle) self.title = newTitle end
      function menuBarItem:delete() self.deleted = true end
      table.insert(createdMenuBars, menuBarItem)
      return menuBarItem
    end,
  },
  styledtext = {
    new = function(text, attributes)
      return setmetatable(
        {
          segments = {
            {
              text = text,
              color = attributes and attributes.color or nil,
              backgroundColor = attributes and attributes.backgroundColor or nil,
              font = attributes and attributes.font or nil,
            },
          },
        },
        styledTextMeta
      )
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

local function segmentForCellText(styledTitle, cellText)
  for _, segment in ipairs(styledTitle.segments) do
    if segment.text == cellText then
      return segment
    end
  end
  return nil
end

local function titleCharacterWidth(styledTitle)
  local parts = {}
  for _, segment in ipairs(styledTitle.segments) do
    table.insert(parts, segment.text)
  end
  return #table.concat(parts)
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

local thirdRowCells = menuBar.cellsForRow(18, 7, { [18] = true })
expectEqual("the third row holds its own seven workspaces", "15 16 17 18 19 20 21", workspaceNumbers(thirdRowCells))

menuBar.render(2, 7, { [2] = true, [5] = true })
expectEqual("first load shows exactly one indicator", 1, liveMenuBarCount())
expectEqual("a single-digit number is centered in its three-character cell", " 1 ", segmentForCellText(createdMenuBars[1].title, " 1 ") and " 1 " or nil)
expectEqual("the active workspace carries the accent background", "controlAccentColor", segmentForCellText(createdMenuBars[1].title, " 2 ").backgroundColor.name)
expectEqual("the active workspace text contrasts against the accent", "selectedMenuItemTextColor", segmentForCellText(createdMenuBars[1].title, " 2 ").color.name)
expectEqual("an occupied workspace uses the accent text color", "controlAccentColor", segmentForCellText(createdMenuBars[1].title, " 5 ").color.name)
expectEqual("an unoccupied workspace uses the auto-following label color", "labelColor", segmentForCellText(createdMenuBars[1].title, " 1 ").color.name)
expectEqual("every cell is drawn in a monospaced font", "Menlo", segmentForCellText(createdMenuBars[1].title, " 1 ").font.name)

local singleDigitRowWidth = titleCharacterWidth(createdMenuBars[1].title)

menuBar.render(18, 7, { [18] = true })
expectEqual(
  "the grid keeps a constant character width across rows so it never resizes",
  singleDigitRowWidth,
  titleCharacterWidth(createdMenuBars[1].title)
)

local function simulateReload()
  menuBar.deleteIndicator()
  package.loaded["workspace_grid_menubar"] = nil
  menuBar = require("workspace_grid_menubar")
end

simulateReload()
menuBar.render(1, 7)
expectEqual("a reload leaves exactly one indicator, no orphan frozen at the old workspace", 1, liveMenuBarCount())
expectEqual(
  "the live workspace is the one highlighted after reload",
  "controlAccentColor",
  segmentForCellText(createdMenuBars[#createdMenuBars].title, " 1 ").backgroundColor.name
)

os.exit(failureCount == 0 and 0 or 1)
