local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local figureSpace = "\u{2007}"

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

local function plainTitle(styledTitle)
  local parts = {}
  for _, segment in ipairs(styledTitle.segments) do
    table.insert(parts, segment.text)
  end
  return (table.concat(parts):gsub(figureSpace, " "))
end

local function titleCharacterWidth(styledTitle)
  local plain = {}
  for _, segment in ipairs(styledTitle.segments) do
    table.insert(plain, segment.text)
  end
  return utf8.len(table.concat(plain))
end

local function cellSegment(styledTitle, firstWorkspaceInRow, workspaceNumber)
  return styledTitle.segments[(workspaceNumber - firstWorkspaceInRow) + 2]
end

local function cellColorName(styledTitle, firstWorkspaceInRow, workspaceNumber)
  local segment = cellSegment(styledTitle, firstWorkspaceInRow, workspaceNumber)
  return segment and segment.color and segment.color.name or nil
end

local function cellBackgroundName(styledTitle, firstWorkspaceInRow, workspaceNumber)
  local segment = cellSegment(styledTitle, firstWorkspaceInRow, workspaceNumber)
  return segment and segment.backgroundColor and segment.backgroundColor.name or nil
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

menuBar.render(2, 7, { [2] = true, [5] = true })
expectEqual("first load shows exactly one indicator", 1, liveMenuBarCount())
expectEqual(
  "every cell has the same width so numbers keep a fixed position",
  "  1   2   3   4   5   6   7 ",
  plainTitle(createdMenuBars[1].title)
)
expectEqual("the active workspace gets the accent background", "controlAccentColor", cellBackgroundName(createdMenuBars[1].title, 1, 2))
expectEqual("the active workspace text contrasts against the accent", "selectedMenuItemTextColor", cellColorName(createdMenuBars[1].title, 1, 2))
expectEqual("an occupied workspace uses the accent text color", "controlAccentColor", cellColorName(createdMenuBars[1].title, 1, 5))
expectEqual("an occupied workspace has no background", nil, cellBackgroundName(createdMenuBars[1].title, 1, 5))
expectEqual("an unoccupied workspace uses the solid label color", "labelColor", cellColorName(createdMenuBars[1].title, 1, 1))

local firstRowCharacterWidth = titleCharacterWidth(createdMenuBars[1].title)
menuBar.render(18, 7, { [18] = true })
expectEqual(
  "the third row shows its own seven workspaces",
  " 15  16  17  18  19  20  21 ",
  plainTitle(createdMenuBars[1].title)
)
expectEqual(
  "every row renders to the same character width",
  firstRowCharacterWidth,
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
  "the surviving indicator shows the live workspace, not a stale one",
  "  1   2   3   4   5   6   7 ",
  plainTitle(createdMenuBars[#createdMenuBars].title)
)
expectEqual(
  "the live workspace is the one highlighted after reload",
  "controlAccentColor",
  cellBackgroundName(createdMenuBars[#createdMenuBars].title, 1, 1)
)

os.exit(failureCount == 0 and 0 or 1)
