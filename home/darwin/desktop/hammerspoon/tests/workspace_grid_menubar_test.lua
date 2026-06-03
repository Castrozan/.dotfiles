-- Reproduces the stale-menubar bug: Hammerspoon reloads on every config redeploy,
-- and each load creates a new menu-bar item. Without deleting the old one, orphaned
-- indicators linger frozen at the workspace they showed at reload time, so the bar
-- can show a workspace different from the live one. deleteIndicator() (called from
-- hs.shutdownCallback) must remove it so a reload leaves exactly one indicator.

local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local lastMenuBar = nil
hs = {
  menubar = {
    new = function()
      lastMenuBar = { deleted = false, title = nil }
      function lastMenuBar:setTitle(newTitle) self.title = newTitle end
      function lastMenuBar:delete() self.deleted = true end
      return lastMenuBar
    end,
  },
}

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
expectEqual("active workspace is bracketed in the title", "1 [2] 3 4 5 6 7", lastMenuBar.title)

menuBar.deleteIndicator()
expectEqual("deleteIndicator removes the menu-bar item", true, lastMenuBar.deleted)

lastMenuBar.title = "untouched"
menuBar.render(1, 7)
expectEqual("render after delete is a safe no-op (no stale orphan left behind)", "untouched", lastMenuBar.title)

os.exit(failureCount == 0 and 0 or 1)
