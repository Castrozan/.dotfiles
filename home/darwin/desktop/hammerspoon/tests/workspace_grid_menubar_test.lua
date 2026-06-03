-- Reproduces the stale-menubar bug: Hammerspoon reloads on every config redeploy,
-- and each load creates a new menu-bar item. Without deleting the old one on the way
-- out, orphaned indicators pile up frozen at the workspace they showed at reload time,
-- so the bar can display a workspace different from the live one. A reload must leave
-- exactly one indicator, showing the live workspace.

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

menuBar.render(2, 7)
expectEqual("first load shows exactly one indicator", 1, liveMenuBarCount())
expectEqual("the indicator brackets the active workspace", "1 [2] 3 4 5 6 7", createdMenuBars[1].title)

-- A config redeploy reloads Hammerspoon: hs.shutdownCallback deletes the old indicator
-- (init.lua wires it to deleteIndicator), then a fresh require creates a new one.
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
  "[1] 2 3 4 5 6 7",
  createdMenuBars[#createdMenuBars].title
)

os.exit(failureCount == 0 and 0 or 1)
