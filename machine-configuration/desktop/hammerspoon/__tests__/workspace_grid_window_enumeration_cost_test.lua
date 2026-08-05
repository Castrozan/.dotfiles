local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local accessibilityEnumerationCallCount = 0
local perApplicationWindowLookupCallCount = 0
local windowServerListCallCount = 0

local windows = harness.setLiveWindowsToIds({ 401, 402, 403 })
local windowServerEntries = harness.windowServerEntriesForWindows(windows)

hs.window.allWindows = function()
	accessibilityEnumerationCallCount = accessibilityEnumerationCallCount + 1
	return windows
end
hs.window.get = function(windowId)
	perApplicationWindowLookupCallCount = perApplicationWindowLookupCallCount + 1
	for _, window in ipairs(windows) do
		if window:id() == windowId then
			return window
		end
	end
	return nil
end
hs.window.find = hs.window.get
hs.window.windowForID = hs.window.get
hs.window.visibleWindows = hs.window.allWindows
hs.window.orderedWindows = hs.window.allWindows
hs.window.list = function()
	windowServerListCallCount = windowServerListCallCount + 1
	return windowServerEntries
end

local grid = harness.loadFreshGrid()
local windowQuery = require("workspace_grid_window_query")

grid.setSessionGenerationTokenForTest("boot-token-stable")
grid.registerExistingWindowsOnDefaultWorkspace()
windows[1]:focus()
grid.moveFocusedWindowToWorkspace(3)
grid.switchToWorkspace(11)
grid.switchToWorkspace(3)
grid.currentWorkspaceWindowList()
grid.focusWindowById(401)
grid.revealWindowById(401)
grid.gatherAllWindowsToCurrentWorkspace()
grid.onWindowCreated(windows[2])
grid.onWindowFocused(windows[2])
grid.onWindowDestroyed(windows[3])
windowQuery.manageableWindows()
windowQuery.occupiedWorkspaceNumbers()
windowQuery.windowDescriptorsByWorkspace()
windowQuery.windowIsNoLongerManageable(403)

expectEqual(
	"no grid path queries every application over accessibility (hs.window.allWindows and friends"
		.. " cost 30-100ms a call, so a single one on a hotkey path doubles a workspace switch)",
	0,
	accessibilityEnumerationCallCount
)

expectEqual(
	"no grid path resolves a window id through hs.window.get, hs.window.find or hs.window.windowForID"
		.. " (all three enumerate every application over accessibility; the window filter already"
		.. " holds the object)",
	0,
	perApplicationWindowLookupCallCount
)

expectEqual("the window server list is what answers window liveness instead", true, windowServerListCallCount > 0)

local windowServerListCallCountBeforeOneSwitch = windowServerListCallCount
grid.switchToWorkspace(5)
local windowServerListCallsPerSwitch = windowServerListCallCount - windowServerListCallCountBeforeOneSwitch
expectEqual(
	"one workspace switch enumerates the window server at most twice (the switch loop and the"
		.. " menu-bar occupancy render); a third means a caller stopped reusing the enumeration",
	true,
	windowServerListCallsPerSwitch <= 2
)

harness.exitWithAccumulatedStatus()
