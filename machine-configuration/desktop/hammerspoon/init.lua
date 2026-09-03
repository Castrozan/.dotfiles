require("hs.ipc")

-- Wiring only: bind the prior AeroSpace keybinds to the virtual-workspace grid
-- defined in workspace_grid.lua, and feed it window create/focus events.
local workspaceGrid = require("workspace_grid")
local menuBarIndicator = require("workspace_grid_menubar")
local menuBarReveal = require("workspace_grid_menu_bar_reveal")
local windowMenu = require("workspace_grid_window_menu")
local windowMenuBarItem = require("workspace_grid_window_menu_bar_item")
local windowSnapshot = require("workspace_grid_window_snapshot")
local chromeProfileWindow = require("chrome_profile_window")
local browserAwareDigitKeybindings = require("workspace_grid_browser_aware_digit_keybindings")
local weztermSummon = require("wezterm_summon")

windowMenuBarItem.installMenuItemBuilder(windowMenu.buildMenuItemBuilder({
	snapshotForImmediateUse = windowSnapshot.snapshotForImmediateUse,
	currentWorkspaceNumber = workspaceGrid.currentWorkspaceNumber,
	revealWindowById = workspaceGrid.revealWindowById,
}))

hs.shutdownCallback = function()
	menuBarReveal.cancel()
	menuBarIndicator.deleteIndicator()
	windowMenuBarItem.deleteMenuBarItem()
end

local workspaceRowSwitchModifiers = { { "cmd" }, { "cmd", "alt" }, { "cmd", "ctrl" } }
local workspaceColumnByKeyCode = {}
for columnNumber = 1, workspaceGrid.columns do
	workspaceColumnByKeyCode[hs.keycodes.map[tostring(columnNumber)]] = columnNumber
end

browserAwareDigitKeybindings.install({
	workspaceGrid = workspaceGrid,
	workspaceColumnByKeyCode = workspaceColumnByKeyCode,
})
require("workspace_grid_two_window_tiling_hotkeys").install(workspaceGrid)

for rowIndex = 1, #workspaceRowSwitchModifiers - 1 do
	for columnNumber = 1, workspaceGrid.columns do
		local targetWorkspaceNumber = rowIndex * workspaceGrid.columns + columnNumber
		hs.hotkey.bind(workspaceRowSwitchModifiers[rowIndex + 1], tostring(columnNumber), function()
			workspaceGrid.switchToWorkspace(targetWorkspaceNumber)
		end)
	end
end

hs.hotkey.bind({ "cmd", "ctrl" }, "m", function()
	menuBarReveal.brieflyReveal()
end)

hs.hotkey.bind({ "cmd", "ctrl", "alt" }, "g", function()
	workspaceGrid.gatherAllWindowsToCurrentWorkspace()
end)

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

require("smart_home_media_key_control").start()

require("prevent_window_minimize").start()

-- Summon is triggered from karabiner (Cmd+B / Cmd+C) rather than an hs.hotkey,
-- because karabiner remaps Ctrl+C to Cmd+C: a global Cmd+C hotkey here would also
-- catch the remapped Ctrl+C and steal copy. Karabiner matches Cmd+C before that
-- remap and invokes these via `hs -c`, so Ctrl+C still copies.
function summonPersonalChromeToCurrentWorkspace()
	workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace(
		"com.google.Chrome",
		"summon-chrome-personal-profile",
		chromeProfileWindow.windowBelongsToPersonalProfile
	)
end
function summonWorkChromeToCurrentWorkspace()
	workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace(
		"com.google.Chrome",
		"summon-chrome-work-profile",
		chromeProfileWindow.windowBelongsToWorkProfile
	)
end
function summonWezTermToCurrentWorkspace()
	weztermSummon.summonToCurrentWorkspace(workspaceGrid)
end
function toggleTwoWindowTiling()
	return workspaceGrid.toggleTwoWindowTiling()
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
windowEventWatcher:subscribe(hs.window.filter.windowUnfullscreened, function(window)
	workspaceGrid.onWindowLeftFullScreen(window)
end)

workspaceGrid.restorePersistedWorkspaceState()
workspaceGrid.registerExistingWindowsOnDefaultWorkspace()
workspaceGrid.switchToWorkspace(workspaceGrid.currentWorkspaceNumber(), hs.window.focusedWindow())

function currentWorkspaceForTest()
	return workspaceGrid.currentWorkspaceNumber()
end

function switchToWorkspaceForTest(targetWorkspaceNumber)
	workspaceGrid.switchToWorkspace(targetWorkspaceNumber)
	return workspaceGrid.currentWorkspaceNumber()
end

hs.alert.show("virtual-workspace grid loaded (7x3)")
