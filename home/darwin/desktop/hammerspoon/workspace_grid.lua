local workspaceGrid = {}

local workspaceGridColumns = 7
local workspaceGridRows = 3
local totalWorkspaceCount = workspaceGridColumns * workspaceGridRows
local defaultWorkspaceNumber = 11

workspaceGrid.columns = workspaceGridColumns
workspaceGrid.totalWorkspaceCount = totalWorkspaceCount

local currentWorkspaceNumber = defaultWorkspaceNumber
local menuBarIndicator = require("workspace_grid_menubar")
local workspaceGridPersistence = require("workspace_grid_persistence")
local windowLayout = require("workspace_grid_window_layout")
local sessionGeneration = require("workspace_grid_session_generation")
local windowAssignment = require("workspace_grid_window_assignment")
local windowQuery = require("workspace_grid_window_query")
local windowSnapshot = require("workspace_grid_window_snapshot")
local navigation = require("workspace_grid_navigation")
local pinnedWindow = require("workspace_grid_pinned_window")

local manageableWindows = windowQuery.manageableWindows

function workspaceGrid.setSessionGenerationTokenForTest(token)
	sessionGeneration.setTokenForTest(token)
end

local function persistWorkspaceState()
	workspaceGridPersistence.save(
		currentWorkspaceNumber,
		sessionGeneration.currentToken(),
		windowAssignment.allWorkspaceNumbersByWindowId()
	)
end

local function renderMenuBarIndicator()
	menuBarIndicator.render(currentWorkspaceNumber, workspaceGridColumns, windowQuery.occupiedWorkspaceNumbers())
end

function workspaceGrid.switchToWorkspace(targetWorkspaceNumber, preferredFocusWindow)
	if targetWorkspaceNumber < 1 or targetWorkspaceNumber > totalWorkspaceCount then
		return
	end
	currentWorkspaceNumber = targetWorkspaceNumber
	local rememberedFocusWindowId = windowAssignment.rememberedFocusedWindowId(targetWorkspaceNumber)
	local rememberedFocusWindow = nil
	local firstTileableWindow = nil
	for _, window in ipairs(manageableWindows()) do
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
	persistWorkspaceState()
end

function workspaceGrid.moveFocusedWindowToWorkspace(targetWorkspaceNumber)
	local focused = hs.window.focusedWindow()
	if not focused then
		return
	end
	if pinnedWindow.windowIsPinned(focused) then
		workspaceGrid.switchToWorkspace(targetWorkspaceNumber)
		return
	end
	windowAssignment.assignWindowToWorkspace(focused:id(), targetWorkspaceNumber)
	workspaceGrid.switchToWorkspace(targetWorkspaceNumber, focused)
end

function workspaceGrid.navigateWorkspace(deltaWithinGrid, alsoMoveFocusedWindow)
	local target = navigation.wrapWorkspaceNumber(currentWorkspaceNumber, deltaWithinGrid, totalWorkspaceCount)
	if alsoMoveFocusedWindow then
		workspaceGrid.moveFocusedWindowToWorkspace(target)
	else
		workspaceGrid.switchToWorkspace(target)
	end
end

local function placeSummonedWindowOnCurrentWorkspace(window)
	windowAssignment.assignWindowToWorkspace(window:id(), currentWorkspaceNumber)
	windowLayout.showWindowOnScreen(window)
	window:focus()
	renderMenuBarIndicator()
	persistWorkspaceState()
end

local summonToWorkspaceEntryPoints = require("workspace_grid_summon_to_workspace").buildSummonToWorkspaceEntryPoints(
	placeSummonedWindowOnCurrentWorkspace
)
workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace =
	summonToWorkspaceEntryPoints.summonApplicationProfileWindowToCurrentWorkspace

function workspaceGrid.gatherAllWindowsToCurrentWorkspace()
	for _, window in ipairs(manageableWindows()) do
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
	persistWorkspaceState()
end

function workspaceGrid.currentWorkspaceWindowList()
	return windowSnapshot.windowListForWorkspace(currentWorkspaceNumber)
end

local windowFocusEntryPoints = require("workspace_grid_window_focus").buildWindowFocusEntryPoints({
	currentWorkspaceNumber = function()
		return currentWorkspaceNumber
	end,
	switchToWorkspace = workspaceGrid.switchToWorkspace,
	persistWorkspaceState = persistWorkspaceState,
})
workspaceGrid.focusWindowById = windowFocusEntryPoints.focusWindowById
workspaceGrid.revealWindowById = windowFocusEntryPoints.revealWindowById

local windowEventHandlers = require("workspace_grid_window_events").buildWindowEventHandlers({
	currentWorkspaceNumber = function()
		return currentWorkspaceNumber
	end,
	renderMenuBarIndicator = renderMenuBarIndicator,
	persistWorkspaceState = persistWorkspaceState,
})
workspaceGrid.onWindowCreated = windowEventHandlers.onWindowCreated
workspaceGrid.onWindowDestroyed = windowEventHandlers.onWindowDestroyed
workspaceGrid.onWindowFocused = windowEventHandlers.onWindowFocused
workspaceGrid.onWindowLeftFullScreen = windowEventHandlers.onWindowLeftFullScreen

function workspaceGrid.registerExistingWindowsOnDefaultWorkspace()
	for _, window in ipairs(manageableWindows()) do
		if not windowAssignment.isWindowAssigned(window:id()) then
			windowAssignment.assignWindowToWorkspace(window:id(), defaultWorkspaceNumber)
		end
	end
	renderMenuBarIndicator()
end

function workspaceGrid.restorePersistedWorkspaceState()
	local restoredCurrentWorkspaceNumber, restoredSessionGenerationToken, restoredAssignments =
		workspaceGridPersistence.load()
	if restoredSessionGenerationToken ~= nil and restoredSessionGenerationToken ~= sessionGeneration.currentToken() then
		currentWorkspaceNumber = defaultWorkspaceNumber
		return
	end
	currentWorkspaceNumber = restoredCurrentWorkspaceNumber or currentWorkspaceNumber
	windowAssignment.adoptPersistedAssignments(restoredAssignments)
end

function workspaceGrid.currentWorkspaceNumber()
	return currentWorkspaceNumber
end

return workspaceGrid
