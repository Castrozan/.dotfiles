local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
harness.setLiveWindowsToIds({ 101 })

local grid = harness.loadFreshGrid()
grid.registerExistingWindowsOnDefaultWorkspace()
local menuBarReveal = require("workspace_grid_menu_bar_reveal")
local revealCount = 0
menuBarReveal.brieflyReveal = function()
	revealCount = revealCount + 1
end

grid.switchToWorkspace(grid.currentWorkspaceNumber())
harness.expectEqual("reselecting the current workspace does not reveal the menu bar", 0, revealCount)

grid.switchToWorkspace(3)
harness.expectEqual("switching to another workspace reveals the menu bar once", 1, revealCount)

grid.switchToWorkspace(22)
harness.expectEqual("an invalid workspace does not reveal the menu bar", 1, revealCount)

grid.focusWindowById(101)
harness.expectEqual("switching to a valid window reveals the menu bar once", 2, revealCount)

grid.focusWindowById(999)
harness.expectEqual("a stale window switch request does not reveal the menu bar", 2, revealCount)

harness.exitWithAccumulatedStatus()
