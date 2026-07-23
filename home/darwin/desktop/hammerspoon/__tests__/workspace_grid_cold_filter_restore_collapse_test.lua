local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windowsBeforeReload = harness.setLiveWindowsToIds({ 101, 102, 103 })

local grid = harness.loadFreshGrid()
grid.setSessionGenerationTokenForTest("boot-token-stable")
grid.registerExistingWindowsOnDefaultWorkspace()
windowsBeforeReload[1]:focus()
grid.moveFocusedWindowToWorkspace(3)
windowsBeforeReload[2]:focus()
grid.moveFocusedWindowToWorkspace(5)
windowsBeforeReload[3]:focus()
grid.moveFocusedWindowToWorkspace(7)
grid.switchToWorkspace(3)
expectEqual("window 101 sits on workspace 3 before the reload", 1, #grid.currentWorkspaceWindowList().windows)

harness.setLiveWindowsToIds({ 101, 102, 103 })
harness.setFilterVisibleWindowIds({})

local reloadedGrid = harness.loadFreshGrid()
reloadedGrid.setSessionGenerationTokenForTest("boot-token-stable")
reloadedGrid.restorePersistedWorkspaceState()
reloadedGrid.registerExistingWindowsOnDefaultWorkspace()
reloadedGrid.switchToWorkspace(reloadedGrid.currentWorkspaceNumber())

harness.setFilterVisibleWindowIds(nil)

reloadedGrid.switchToWorkspace(3)
local windowsOnWorkspaceThreeAfterReload = reloadedGrid.currentWorkspaceWindowList().windows
expectEqual(
	"window 101 keeps workspace 3 across a reload where the window filter was cold at restore",
	1,
	#windowsOnWorkspaceThreeAfterReload
)
expectEqual(
	"window 101 did not collapse onto the default workspace 11",
	101,
	windowsOnWorkspaceThreeAfterReload[1] and windowsOnWorkspaceThreeAfterReload[1]["window-id"] or -1
)

reloadedGrid.switchToWorkspace(5)
expectEqual(
	"window 102 keeps workspace 5 across the cold-filter reload",
	1,
	#reloadedGrid.currentWorkspaceWindowList().windows
)

reloadedGrid.switchToWorkspace(11)
expectEqual(
	"the default workspace 11 did not absorb every window after the cold-filter reload",
	0,
	#reloadedGrid.currentWorkspaceWindowList().windows
)

harness.exitWithAccumulatedStatus()
