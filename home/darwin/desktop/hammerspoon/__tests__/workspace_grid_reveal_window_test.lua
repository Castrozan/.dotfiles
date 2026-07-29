local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windows = harness.setLiveWindowsToIds({ 101, 102 })

local grid = harness.loadFreshGrid()
grid.registerExistingWindowsOnDefaultWorkspace()
windows[2]:focus()
grid.moveFocusedWindowToWorkspace(5)
grid.switchToWorkspace(3)
windows[1]:focus()
grid.moveFocusedWindowToWorkspace(3)

expectEqual("the grid starts on workspace 3", 3, grid.currentWorkspaceNumber())

grid.revealWindowById(102)
expectEqual("revealing a window that lives elsewhere switches to its workspace", 5, grid.currentWorkspaceNumber())
expectEqual(
	"the revealed window stays on its own workspace instead of being dragged to the one in view",
	102,
	grid.currentWorkspaceWindowList().windows[1] and grid.currentWorkspaceWindowList().windows[1]["window-id"] or -1
)
expectEqual("workspace 5 holds only the window that already lived there", 1, #grid.currentWorkspaceWindowList().windows)

grid.revealWindowById(102)
expectEqual("revealing a window already in view leaves the workspace alone", 5, grid.currentWorkspaceNumber())
expectEqual("revealing a window already in view focuses it", 102, hs.window.focusedWindow():id())

grid.focusWindowById(101)
expectEqual(
	"the switcher focus path still pulls a window from another workspace into the one in view",
	5,
	grid.currentWorkspaceNumber()
)
expectEqual("the pulled window joins the workspace in view", 2, #grid.currentWorkspaceWindowList().windows)

harness.exitWithAccumulatedStatus()
