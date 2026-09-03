local workspaceGrid = {}

local workspaceGridColumns = 7
local workspaceGridRows = 3
local totalWorkspaceCount = workspaceGridColumns * workspaceGridRows
local defaultWorkspaceNumber = 11

workspaceGrid.columns = workspaceGridColumns
workspaceGrid.totalWorkspaceCount = totalWorkspaceCount

local currentWorkspaceNumber = defaultWorkspaceNumber
local menuBarIndicator = require("workspace_grid_menubar")
local menuBarReveal = require("workspace_grid_menu_bar_reveal")
local workspaceGridPersistence = require("workspace_grid_persistence")
local windowLayout = require("workspace_grid_window_layout")
local sessionGeneration = require("workspace_grid_session_generation")
local windowAssignment = require("workspace_grid_window_assignment")
local windowQuery = require("workspace_grid_window_query")
local windowSnapshot = require("workspace_grid_window_snapshot")
local navigation = require("workspace_grid_navigation")
local pinnedWindow = require("workspace_grid_pinned_window")
local twoWindowTiling = require("workspace_grid_two_window_tiling")

local function readCurrentWorkspaceNumber()
	return currentWorkspaceNumber
end

function workspaceGrid.setSessionGenerationTokenForTest(token)
	sessionGeneration.setTokenForTest(token)
end

local workspaceLayoutChangeObservers = {}

local function persistWorkspaceState()
	workspaceGridPersistence.save(
		currentWorkspaceNumber,
		sessionGeneration.currentToken(),
		windowAssignment.allWorkspaceNumbersByWindowId()
	)
end

local function onWorkspaceLayoutChanged()
	persistWorkspaceState()
	for _, observer in ipairs(workspaceLayoutChangeObservers) do
		observer()
	end
end

function workspaceGrid.observeWorkspaceLayoutChanges(observer)
	table.insert(workspaceLayoutChangeObservers, observer)
end

local function renderMenuBarIndicator()
	menuBarIndicator.render(currentWorkspaceNumber, workspaceGridColumns, windowQuery.occupiedWorkspaceNumbers())
end

function workspaceGrid.switchToWorkspace(targetWorkspaceNumber, preferredFocusWindow)
	if targetWorkspaceNumber < 1 or targetWorkspaceNumber > totalWorkspaceCount then
		return
	end
	twoWindowTiling.deactivate()
	local workspaceChanged = targetWorkspaceNumber ~= currentWorkspaceNumber
	currentWorkspaceNumber = targetWorkspaceNumber
	local rememberedFocusWindowId = windowAssignment.rememberedFocusedWindowId(targetWorkspaceNumber)
	local rememberedFocusWindow = nil
	local firstTileableWindow = nil
	for _, window in ipairs(windowQuery.manageableWindows()) do
		if windowAssignment.workspaceOfWindowId(window:id()) == targetWorkspaceNumber then
			windowLayout.showWindowOnScreen(window)
			if windowLayout.windowIsTileable(window) then
				firstTileableWindow = firstTileableWindow or window
				if window:id() == rememberedFocusWindowId then
					rememberedFocusWindow = window
				end
			end
		else
			windowLayout.parkWindowOffScreen(window)
		end
	end
	local windowToRefocus = preferredFocusWindow or rememberedFocusWindow or firstTileableWindow
	if windowToRefocus then
		windowToRefocus:focus()
		windowAssignment.rememberFocusedWindow(targetWorkspaceNumber, windowToRefocus:id())
	end
	renderMenuBarIndicator()
	if workspaceChanged then
		menuBarReveal.brieflyReveal()
	end
	onWorkspaceLayoutChanged()
end

local navigationEntryPoints = navigation.buildNavigationEntryPoints({
	currentWorkspaceNumber = readCurrentWorkspaceNumber,
	totalWorkspaceCount = totalWorkspaceCount,
	switchToWorkspace = workspaceGrid.switchToWorkspace,
})
workspaceGrid.moveFocusedWindowToWorkspace = navigationEntryPoints.moveFocusedWindowToWorkspace
workspaceGrid.navigateWorkspace = navigationEntryPoints.navigateWorkspace

local function placeSummonedWindowOnCurrentWorkspace(window)
	twoWindowTiling.deactivate()
	windowAssignment.assignWindowToWorkspace(window:id(), currentWorkspaceNumber)
	windowLayout.showWindowOnScreen(window)
	window:focus()
	renderMenuBarIndicator()
	onWorkspaceLayoutChanged()
end

local summonToWorkspaceEntryPoints = require("workspace_grid_summon_to_workspace").buildSummonToWorkspaceEntryPoints(
	placeSummonedWindowOnCurrentWorkspace
)
workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace =
	summonToWorkspaceEntryPoints.summonApplicationProfileWindowToCurrentWorkspace

function workspaceGrid.gatherAllWindowsToCurrentWorkspace()
	twoWindowTiling.deactivate()
	for _, window in ipairs(windowQuery.manageableWindows()) do
		if not pinnedWindow.windowIsPinned(window) then
			windowAssignment.assignWindowToWorkspace(window:id(), currentWorkspaceNumber)
			windowLayout.showWindowOnScreen(window)
		end
	end
	local focusedWindow = hs.window.focusedWindow()
	if focusedWindow then
		windowAssignment.rememberFocusedWindow(currentWorkspaceNumber, focusedWindow:id())
	end
	renderMenuBarIndicator()
	onWorkspaceLayoutChanged()
end

function workspaceGrid.currentWorkspaceWindowList()
	return windowSnapshot.windowListForWorkspace(currentWorkspaceNumber)
end

require("workspace_grid_two_window_tiling_entry_points").install(workspaceGrid, {
	currentWorkspaceNumber = readCurrentWorkspaceNumber,
	onWorkspaceLayoutChanged = onWorkspaceLayoutChanged,
})

local windowFocusEntryPoints = require("workspace_grid_window_focus").buildWindowFocusEntryPoints({
	currentWorkspaceNumber = readCurrentWorkspaceNumber,
	switchToWorkspace = workspaceGrid.switchToWorkspace,
	onWorkspaceLayoutChanged = onWorkspaceLayoutChanged,
	revealMenuBar = function()
		menuBarReveal.brieflyReveal()
	end,
})
workspaceGrid.focusWindowById = windowFocusEntryPoints.focusWindowById
workspaceGrid.revealWindowById = windowFocusEntryPoints.revealWindowById

local windowEventHandlers = require("workspace_grid_window_events").buildWindowEventHandlers({
	currentWorkspaceNumber = readCurrentWorkspaceNumber,
	renderMenuBarIndicator = renderMenuBarIndicator,
	onWorkspaceLayoutChanged = onWorkspaceLayoutChanged,
})
workspaceGrid.onWindowCreated = windowEventHandlers.onWindowCreated
workspaceGrid.onWindowDestroyed = windowEventHandlers.onWindowDestroyed
workspaceGrid.onWindowFocused = windowEventHandlers.onWindowFocused
workspaceGrid.onWindowLeftFullScreen = windowEventHandlers.onWindowLeftFullScreen

function workspaceGrid.registerExistingWindowsOnDefaultWorkspace()
	for _, window in ipairs(windowQuery.manageableWindows()) do
		if not windowAssignment.isWindowAssigned(window:id()) then
			windowAssignment.assignWindowToWorkspace(window:id(), defaultWorkspaceNumber)
		end
	end
	renderMenuBarIndicator()
end

function workspaceGrid.restorePersistedWorkspaceState()
	local restoredCurrentWorkspaceNumber, restoredSessionGenerationToken, restoredAssignments =
		workspaceGridPersistence.load()
	local liveSessionGenerationToken = sessionGeneration.currentToken()
	if
		restoredSessionGenerationToken ~= nil
		and liveSessionGenerationToken ~= nil
		and restoredSessionGenerationToken ~= liveSessionGenerationToken
	then
		currentWorkspaceNumber = defaultWorkspaceNumber
		return
	end
	currentWorkspaceNumber = restoredCurrentWorkspaceNumber or currentWorkspaceNumber
	windowAssignment.adoptPersistedAssignments(restoredAssignments)
end

workspaceGrid.currentWorkspaceNumber = readCurrentWorkspaceNumber

return workspaceGrid
