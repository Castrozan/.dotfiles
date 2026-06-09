local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "tests/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windows = harness.setLiveWindowsToIds({ 101, 102, 103 })

local grid = harness.loadFreshGrid()
grid.registerExistingWindowsOnDefaultWorkspace()
windows[2]:focus()
grid.moveFocusedWindowToWorkspace(3)
grid.switchToWorkspace(2)
expectEqual("active workspace is 2 before reload", 2, grid.currentWorkspaceNumber())

local reloadedGrid = harness.loadFreshGrid()
reloadedGrid.restorePersistedWorkspaceState()

expectEqual("active workspace 2 survives the reload", 2, reloadedGrid.currentWorkspaceNumber())
reloadedGrid.switchToWorkspace(3)
local windowsOnWorkspaceThree = reloadedGrid.currentWorkspaceWindowList().windows
expectEqual("exactly one window is on workspace 3 after reload", 1, #windowsOnWorkspaceThree)
expectEqual(
	"the window restored onto workspace 3 is 102, not collapsed to the default workspace",
	102,
	windowsOnWorkspaceThree[1] and windowsOnWorkspaceThree[1]["window-id"] or -1
)

local windowsBeforeReboot = harness.setLiveWindowsToIds({ 201, 202, 203 })

local gridBeforeReboot = harness.loadFreshGrid()
gridBeforeReboot.setSessionGenerationTokenForTest("boot-token-before")
gridBeforeReboot.registerExistingWindowsOnDefaultWorkspace()
windowsBeforeReboot[2]:focus()
gridBeforeReboot.moveFocusedWindowToWorkspace(3)

local gridAfterReboot = harness.loadFreshGrid()
gridAfterReboot.setSessionGenerationTokenForTest("boot-token-after")
gridAfterReboot.restorePersistedWorkspaceState()
expectEqual(
	"after a reboot the active workspace resets to the default workspace 11",
	11,
	gridAfterReboot.currentWorkspaceNumber()
)
gridAfterReboot.registerExistingWindowsOnDefaultWorkspace()
gridAfterReboot.switchToWorkspace(3)
expectEqual(
	"after a reboot no window resurrects on workspace 3 from the stale map",
	0,
	#gridAfterReboot.currentWorkspaceWindowList().windows
)

local windowsBeforeClose = harness.setLiveWindowsToIds({ 301, 302 })

local gridWithBothWindows = harness.loadFreshGrid()
gridWithBothWindows.setSessionGenerationTokenForTest("boot-token-stable")
gridWithBothWindows.registerExistingWindowsOnDefaultWorkspace()
windowsBeforeClose[2]:focus()
gridWithBothWindows.moveFocusedWindowToWorkspace(3)

harness.setLiveWindowsToIds({ 301 })

local gridAfterWindowClosed = harness.loadFreshGrid()
gridAfterWindowClosed.setSessionGenerationTokenForTest("boot-token-stable")
gridAfterWindowClosed.restorePersistedWorkspaceState()
gridAfterWindowClosed.switchToWorkspace(3)
expectEqual(
	"a window that closed while unobserved does not resurrect on workspace 3 via recycled id",
	0,
	#gridAfterWindowClosed.currentWorkspaceWindowList().windows
)

harness.setLiveWindowsToIds({ 401, 402 })

local oldFormatStateFile = io.open(harness.stateFilePath(), "w")
oldFormatStateFile:write("2\n")
oldFormatStateFile:write("401 1\n")
oldFormatStateFile:write("402 3\n")
oldFormatStateFile:close()

local gridReadingOldFormat = harness.loadFreshGrid()
gridReadingOldFormat.setSessionGenerationTokenForTest("boot-token-stable")
gridReadingOldFormat.restorePersistedWorkspaceState()
gridReadingOldFormat.registerExistingWindowsOnDefaultWorkspace()
gridReadingOldFormat.switchToWorkspace(3)
local windowsOnWorkspaceThreeFromOldFormat = gridReadingOldFormat.currentWorkspaceWindowList().windows
expectEqual(
	"an old-format state file with no generation line does not collapse every window onto the default workspace",
	1,
	#windowsOnWorkspaceThreeFromOldFormat
)
expectEqual(
	"the old-format assignment is adopted so window 402 stays on workspace 3",
	402,
	windowsOnWorkspaceThreeFromOldFormat[1] and windowsOnWorkspaceThreeFromOldFormat[1]["window-id"] or -1
)

harness.exitWithAccumulatedStatus()
