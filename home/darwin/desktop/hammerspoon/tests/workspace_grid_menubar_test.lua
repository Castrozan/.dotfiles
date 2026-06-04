local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

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
    new = function(text)
      local styledText = { text = text, styles = {} }
      function styledText:setStyle(attributes, startIndex, endIndex)
        table.insert(self.styles, { attributes = attributes, startIndex = startIndex, endIndex = endIndex })
        return self
      end
      return styledText
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

local function cellAlphaForWorkspace(styledText, firstWorkspaceInRow, workspaceNumber)
  local cellStartIndex = (workspaceNumber - firstWorkspaceInRow) * 4 + 1
  for _, style in ipairs(styledText.styles) do
    if style.startIndex == cellStartIndex then
      return style.attributes.color.alpha
    end
  end
  return nil
end

menuBar.render(2, 7, { [2] = true })
expectEqual("first load shows exactly one indicator", 1, liveMenuBarCount())
expectEqual(
  "the indicator brackets the active workspace and pads numbers to a fixed width",
  "  1 [ 2]  3   4   5   6   7 ",
  createdMenuBars[1].title.text
)
expectEqual("the occupied workspace is drawn fully opaque", 1.0, cellAlphaForWorkspace(createdMenuBars[1].title, 1, 2))
expectEqual("an empty workspace is dimmed", 0.35, cellAlphaForWorkspace(createdMenuBars[1].title, 1, 1))

menuBar.render(18, 7, { [18] = true })
expectEqual(
  "the third row shows its own seven workspaces at the same width",
  " 15  16  17 [18] 19  20  21 ",
  createdMenuBars[1].title.text
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
  "[ 1]  2   3   4   5   6   7 ",
  createdMenuBars[#createdMenuBars].title.text
)

os.exit(failureCount == 0 and 0 or 1)
