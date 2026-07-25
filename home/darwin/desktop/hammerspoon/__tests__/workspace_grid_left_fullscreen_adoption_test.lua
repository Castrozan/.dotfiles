local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windows = harness.setLiveWindowsToIds({ 301, 302 })

local grid = harness.loadFreshGrid()
grid.setSessionGenerationTokenForTest("boot-token-stable")
grid.registerExistingWindowsOnDefaultWorkspace()
windows[2]:focus()
grid.moveFocusedWindowToWorkspace(7)
grid.switchToWorkspace(18)

grid.onWindowLeftFullScreen(windows[1])

expectEqual(
	"a window returning from native fullscreen lands on the workspace in view",
	1,
	#grid.currentWorkspaceWindowList().windows
)
expectEqual(
	"the returning window is the one that left fullscreen",
	301,
	grid.currentWorkspaceWindowList().windows[1] and grid.currentWorkspaceWindowList().windows[1]["window-id"] or -1
)
expectEqual("the returning window is shown on screen rather than parked", 0, windows[1]:frame().x)

grid.switchToWorkspace(7)
expectEqual(
	"the workspace the returning window did not belong to is untouched",
	1,
	#grid.currentWorkspaceWindowList().windows
)

harness.exitWithAccumulatedStatus()
