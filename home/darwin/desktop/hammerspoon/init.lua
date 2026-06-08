require("hs.ipc")

-- Wiring only: bind the prior AeroSpace keybinds to the virtual-workspace grid
-- defined in workspace_grid.lua, and feed it window create/focus events.
local workspaceGrid = require("workspace_grid")
local menuBarIndicator = require("workspace_grid_menubar")

hs.shutdownCallback = function()
	menuBarIndicator.deleteIndicator()
end

for columnNumber = 1, workspaceGrid.columns do
	hs.hotkey.bind({ "cmd" }, tostring(columnNumber), function()
		workspaceGrid.switchToWorkspace(columnNumber)
	end)
	hs.hotkey.bind({ "cmd", "shift" }, tostring(columnNumber), function()
		workspaceGrid.moveFocusedWindowToWorkspace(columnNumber)
	end)
end

local navigationDeltasByArrowKey = {
	left = -1,
	right = 1,
	up = -workspaceGrid.columns,
	down = workspaceGrid.columns,
}
for arrowKey, deltaWithinGrid in pairs(navigationDeltasByArrowKey) do
	hs.hotkey.bind({ "ctrl", "alt" }, arrowKey, function()
		workspaceGrid.navigateWorkspace(deltaWithinGrid, false)
	end)
	hs.hotkey.bind({ "ctrl", "alt", "shift" }, arrowKey, function()
		workspaceGrid.navigateWorkspace(deltaWithinGrid, true)
	end)
	hs.hotkey.bind({ "cmd", "alt" }, arrowKey, function()
		workspaceGrid.navigateWorkspace(deltaWithinGrid, false)
	end)
	hs.hotkey.bind({ "cmd", "alt", "shift" }, arrowKey, function()
		workspaceGrid.navigateWorkspace(deltaWithinGrid, true)
	end)
end

-- Cmd+Tab is handled by the Swift window-switcher daemon (overlay + hold-cmd /
-- cycle / release-to-commit), routed via karabiner; this module only feeds it the
-- active workspace's windows and performs the focus it requests.
require("switcher_bridge")

require("karabiner_application_focus_variables").start()

-- Summon is triggered from karabiner (Cmd+B / Cmd+C) rather than an hs.hotkey,
-- because karabiner remaps Ctrl+C to Cmd+C: a global Cmd+C hotkey here would also
-- catch the remapped Ctrl+C and steal copy. Karabiner matches Cmd+C before that
-- remap and invokes these via `hs -c`, so Ctrl+C still copies.
function summonBraveBrowserToCurrentWorkspace()
	workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")
end
function summonGoogleChromeToCurrentWorkspace()
	workspaceGrid.summonApplicationToCurrentWorkspace("Google Chrome", "com.google.Chrome")
end

local windowEventWatcher = hs.window.filter.new()
windowEventWatcher:subscribe(hs.window.filter.windowCreated, function(window)
	workspaceGrid.onWindowCreated(window)
end)
windowEventWatcher:subscribe(hs.window.filter.windowFocused, function(window)
	workspaceGrid.onWindowFocused(window)
end)
windowEventWatcher:subscribe(hs.window.filter.windowDestroyed, function(window)
	workspaceGrid.onWindowDestroyed(window)
end)

workspaceGrid.restorePersistedWorkspaceState()
workspaceGrid.registerExistingWindowsOnFirstWorkspace()
workspaceGrid.switchToWorkspace(workspaceGrid.currentWorkspaceNumber(), hs.window.focusedWindow())

function currentWorkspaceForTest()
	return workspaceGrid.currentWorkspaceNumber()
end

function switchToWorkspaceForTest(targetWorkspaceNumber)
	workspaceGrid.switchToWorkspace(targetWorkspaceNumber)
	return workspaceGrid.currentWorkspaceNumber()
end

hs.alert.show("virtual-workspace grid loaded (7x2)")
