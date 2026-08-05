local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windows = harness.setLiveWindowsToIds({ 201, 202, 203 })

local grid = harness.loadFreshGrid()
grid.setSessionGenerationTokenForTest("boot-token-stable")
grid.registerExistingWindowsOnDefaultWorkspace()
windows[1]:focus()
grid.moveFocusedWindowToWorkspace(3)
windows[2]:focus()
grid.moveFocusedWindowToWorkspace(5)
grid.switchToWorkspace(18)

harness.setWindowServerVisibleWindowIds({})
grid.onWindowCreated(windows[3])
grid.onWindowDestroyed(windows[1])
harness.setWindowServerVisibleWindowIds(nil)

grid.switchToWorkspace(3)
expectEqual(
	"window 201 keeps workspace 3 through a window-server blackout",
	1,
	#grid.currentWorkspaceWindowList().windows
)

grid.switchToWorkspace(5)
expectEqual(
	"window 202 keeps workspace 5 through a window-server blackout",
	1,
	#grid.currentWorkspaceWindowList().windows
)

grid.switchToWorkspace(11)
expectEqual(
	"the default workspace did not absorb the windows the blackout hid",
	0,
	#grid.currentWorkspaceWindowList().windows
)

local reloadedGrid = harness.loadFreshGrid()
local restoredWindowAssignment = require("workspace_grid_window_assignment")
reloadedGrid.setSessionGenerationTokenForTest("boot-token-stable")
reloadedGrid.restorePersistedWorkspaceState()

expectEqual(
	"the state file written during the blackout still places window 201 on workspace 3",
	3,
	restoredWindowAssignment.allWorkspaceNumbersByWindowId()[201]
)
expectEqual(
	"the state file written during the blackout still places window 202 on workspace 5",
	5,
	restoredWindowAssignment.allWorkspaceNumbersByWindowId()[202]
)

harness.setLiveWindowsToIds({ 201, 202 })
reloadedGrid.onWindowDestroyed(windows[3])
expectEqual(
	"a destroyed window the window server confirms is gone still loses its assignment",
	nil,
	restoredWindowAssignment.allWorkspaceNumbersByWindowId()[203]
)
expectEqual(
	"the confirmed destruction left every surviving assignment alone",
	3,
	restoredWindowAssignment.allWorkspaceNumbersByWindowId()[201]
)

harness.exitWithAccumulatedStatus()
