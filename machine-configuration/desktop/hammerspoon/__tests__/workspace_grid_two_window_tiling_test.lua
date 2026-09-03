local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windows = harness.setLiveWindowsToIds({ 101, 102, 103 })
local grid = harness.loadFreshGrid()
grid.registerExistingWindowsOnDefaultWorkspace()
grid.switchToWorkspace(11)

windows[2]:focus()
grid.onWindowFocused(windows[2])
windows[1]:focus()
grid.onWindowFocused(windows[1])

expectEqual("Cmd+E activates two-window tiling", true, grid.toggleTwoWindowTiling())
expectEqual("the current window occupies the left half", 0, windows[1]:frame().x)
expectEqual("the current window uses half the screen width", 720, windows[1]:frame().w)
expectEqual("the previous window occupies the right half", 720, windows[2]:frame().x)
expectEqual("the previous window uses half the screen width", 720, windows[2]:frame().w)
expectEqual("the unpaired window remains maximized", 1440, windows[3]:frame().w)

expectEqual("Cmd+Right is handled while the pair is active", true, grid.focusRightTiledWindow())
expectEqual("Cmd+Right focuses the right window", 102, hs.window.focusedWindow():id())
grid.onWindowFocused(windows[2])
expectEqual("Cmd+Left is handled while the pair is active", true, grid.focusLeftTiledWindow())
expectEqual("Cmd+Left focuses the left window", 101, hs.window.focusedWindow():id())
grid.onWindowFocused(windows[1])

expectEqual("a second Cmd+E restores accordion mode", false, grid.toggleTwoWindowTiling())
expectEqual("the left window returns to full width", 1440, windows[1]:frame().w)
expectEqual("the right window returns to full width", 1440, windows[2]:frame().w)
expectEqual("Cmd+Left passes through outside the pair", false, grid.focusLeftTiledWindow())
expectEqual("Cmd+Right passes through outside the pair", false, grid.focusRightTiledWindow())

windows[2]:focus()
grid.onWindowFocused(windows[2])
windows[1]:focus()
grid.onWindowFocused(windows[1])
grid.onWindowFocused(windows[1])
expectEqual("repeated focus events preserve the previous MRU window", true, grid.toggleTwoWindowTiling())
expectEqual("the preserved previous MRU window remains on the right", 720, windows[2]:frame().x)

windows[3]:focus()
grid.onWindowFocused(windows[3])
expectEqual("focusing a third window leaves two-window mode", false, grid.twoWindowTilingIsActive())
expectEqual("the former left window is maximized after leaving the pair", 1440, windows[1]:frame().w)
expectEqual("the former right window is maximized after leaving the pair", 1440, windows[2]:frame().w)

windows[2]:focus()
grid.onWindowFocused(windows[2])
windows[1]:focus()
grid.onWindowFocused(windows[1])
grid.toggleTwoWindowTiling()
harness.setWindowServerVisibleWindowIds({})
grid.onWindowDestroyed(windows[2])
expectEqual(
	"destroying a pair member during a WindowServer blackout leaves two-window mode",
	false,
	grid.twoWindowTilingIsActive()
)
expectEqual("the surviving pair member is maximized after its peer closes", 1440, windows[1]:frame().w)
harness.setWindowServerVisibleWindowIds(nil)

windows[2]:focus()
grid.onWindowFocused(windows[2])
windows[1]:focus()
grid.onWindowFocused(windows[1])
grid.toggleTwoWindowTiling()
grid.switchToWorkspace(12)
expectEqual("switching workspace leaves two-window mode", false, grid.twoWindowTilingIsActive())

local crossWorkspaceGrid = harness.loadFreshGrid()
crossWorkspaceGrid.registerExistingWindowsOnDefaultWorkspace()
windows[3]:focus()
crossWorkspaceGrid.onWindowFocused(windows[3])
crossWorkspaceGrid.moveFocusedWindowToWorkspace(2)
crossWorkspaceGrid.switchToWorkspace(11)
windows[2]:focus()
crossWorkspaceGrid.onWindowFocused(windows[2])
windows[3]:focus()
crossWorkspaceGrid.onWindowFocused(windows[3])
expectEqual(
	"a window externally focused from another workspace cannot enter the pair",
	false,
	crossWorkspaceGrid.toggleTwoWindowTiling()
)

harness.exitWithAccumulatedStatus()
