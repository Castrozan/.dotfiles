local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windows = harness.setLiveWindowsToIds({ 101, 102 })

hs.execute = function()
	return "E3948995-1019-4E57-AB6A-EAE461B0AF9E\n"
end

local grid = harness.loadFreshGrid()
grid.registerExistingWindowsOnDefaultWorkspace()
windows[1]:focus()
grid.moveFocusedWindowToWorkspace(3)
expectEqual("the grid sits on workspace 3 before the reload", 3, grid.currentWorkspaceNumber())

hs.execute = function()
	return nil
end

local gridAfterFailedProbe = harness.loadFreshGrid()
gridAfterFailedProbe.restorePersistedWorkspaceState()

expectEqual(
	"a boot-session probe that fails mid-reload must not reset the workspace in view",
	3,
	gridAfterFailedProbe.currentWorkspaceNumber()
)
expectEqual(
	"a boot-session probe that fails mid-reload must not flatten the grid onto the default workspace",
	1,
	#gridAfterFailedProbe.currentWorkspaceWindowList().windows
)
expectEqual(
	"the window kept its own workspace instead of falling to the default",
	101,
	gridAfterFailedProbe.currentWorkspaceWindowList().windows[1]
			and gridAfterFailedProbe.currentWorkspaceWindowList().windows[1]["window-id"]
		or -1
)

gridAfterFailedProbe.registerExistingWindowsOnDefaultWorkspace()
gridAfterFailedProbe.switchToWorkspace(3)

hs.execute = function()
	return "E3948995-1019-4E57-AB6A-EAE461B0AF9E\n"
end

local gridAfterProbeRecovered = harness.loadFreshGrid()
gridAfterProbeRecovered.restorePersistedWorkspaceState()
expectEqual(
	"state persisted while the probe was failing still restores once the probe recovers",
	3,
	gridAfterProbeRecovered.currentWorkspaceNumber()
)
gridAfterProbeRecovered.switchToWorkspace(3)

hs.execute = function()
	return "11111111-2222-3333-4444-555555555555\n"
end

local gridAfterReboot = harness.loadFreshGrid()
gridAfterReboot.restorePersistedWorkspaceState()
expectEqual(
	"a genuinely different boot session still discards the stale grid",
	11,
	gridAfterReboot.currentWorkspaceNumber()
)

harness.exitWithAccumulatedStatus()
