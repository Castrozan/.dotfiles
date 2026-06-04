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

local function segmentForWorkspace(styledTitle, workspaceNumber)
  local cellText = figureSpace .. workspaceNumber .. figureSpace
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
  return utf8.len(table.concat(parts))
end

local function cellColorName(styledTitle, workspaceNumber)
  local segment = segmentForWorkspace(styledTitle, workspaceNumber)
  return segment and segment.color and segment.color.name or nil
end

local function cellBackgroundName(styledTitle, workspaceNumber)
  local segment = segmentForWorkspace(styledTitle, workspaceNumber)
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

menuBar.render(2, 7, { [2] = true, [5] = true }, 21)
expectEqual("first load shows exactly one indicator", 1, liveMenuBarCount())
expectEqual(
  "the active number is centered with one figure space on each side",
  figureSpace .. "2" .. figureSpace,
  segmentForWorkspace(createdMenuBars[1].title, 2).text
)
expectEqual("the active workspace gets the accent background", "controlAccentColor", cellBackgroundName(createdMenuBars[1].title, 2))
expectEqual("the active workspace text contrasts against the accent", "selectedMenuItemTextColor", cellColorName(createdMenuBars[1].title, 2))
expectEqual("an occupied workspace uses the accent text color", "controlAccentColor", cellColorName(createdMenuBars[1].title, 5))
expectEqual("an occupied workspace has no background", nil, cellBackgroundName(createdMenuBars[1].title, 5))
expectEqual("an unoccupied workspace uses the solid label color", "labelColor", cellColorName(createdMenuBars[1].title, 1))

local singleDigitRowWidth = titleCharacterWidth(createdMenuBars[1].title)

menuBar.render(18, 7, { [18] = true }, 21)
expectEqual(
  "a double-digit number is centered too",
  figureSpace .. "18" .. figureSpace,
  segmentForWorkspace(createdMenuBars[1].title, 18).text
)
expectEqual(
  "the grid keeps a constant width across rows so it never resizes",
  singleDigitRowWidth,
  titleCharacterWidth(createdMenuBars[1].title)
)

local function simulateReload()
  menuBar.deleteIndicator()
  package.loaded["workspace_grid_menubar"] = nil
  menuBar = require("workspace_grid_menubar")
end

simulateReload()
menuBar.render(1, 7, {}, 21)

expectEqual("a reload leaves exactly one indicator, no orphan frozen at the old workspace", 1, liveMenuBarCount())
expectEqual(
  "the live workspace is the one highlighted after reload",
  "controlAccentColor",
  cellBackgroundName(createdMenuBars[#createdMenuBars].title, 1)
)
expectEqual(
  "the reloaded row keeps the same constant width",
  singleDigitRowWidth,
  titleCharacterWidth(createdMenuBars[#createdMenuBars].title)
)

os.exit(failureCount == 0 and 0 or 1)
