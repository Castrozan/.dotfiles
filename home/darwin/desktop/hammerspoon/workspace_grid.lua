local workspaceGrid = {}

local workspaceGridColumns = 7
local workspaceGridRows = 3
local totalWorkspaceCount = workspaceGridColumns * workspaceGridRows
local firstWorkspaceNumber = 1

workspaceGrid.columns = workspaceGridColumns
workspaceGrid.totalWorkspaceCount = totalWorkspaceCount

local currentWorkspaceNumber = firstWorkspaceNumber
local menuBarIndicator = require("workspace_grid_menubar")
local workspaceGridPersistence = require("workspace_grid_persistence")
local windowLayout = require("workspace_grid_window_layout")
local sessionGeneration = require("workspace_grid_session_generation")
local windowAssignment = require("workspace_grid_window_assignment")
local windowSummon = require("workspace_grid_summon")
local windowQuery = require("workspace_grid_window_query")

local manageableWindows = windowQuery.manageableWindows
local liveWindowExists = windowQuery.liveWindowExists

function workspaceGrid.setSessionGenerationTokenForTest(token)
	sessionGeneration.setTokenForTest(token)
end

local function persistWorkspaceState()
	windowAssignment.forgetWindowsFailingLivenessCheck(liveWindowExists)
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
	windowAssignment.assignWindowToWorkspace(focused:id(), targetWorkspaceNumber)
	workspaceGrid.switchToWorkspace(targetWorkspaceNumber, focused)
end

function workspaceGrid.navigateWorkspace(deltaWithinGrid, alsoMoveFocusedWindow)
	local target = currentWorkspaceNumber + deltaWithinGrid
	if target < 1 then
		target = totalWorkspaceCount + target
	elseif target > totalWorkspaceCount then
		target = target - totalWorkspaceCount
	end
	if alsoMoveFocusedWindow then
		workspaceGrid.moveFocusedWindowToWorkspace(target)
	else
		workspaceGrid.switchToWorkspace(target)
	end
end

function workspaceGrid.summonApplicationToCurrentWorkspace(applicationName, applicationBundleIdentifier)
	windowSummon.summon(applicationName, applicationBundleIdentifier, function(window)
		windowAssignment.assignWindowToWorkspace(window:id(), currentWorkspaceNumber)
		windowLayout.showWindowOnScreen(window)
		window:focus()
		renderMenuBarIndicator()
		persistWorkspaceState()
	end)
end

function workspaceGrid.gatherAllWindowsToCurrentWorkspace()
	for _, window in ipairs(manageableWindows()) do
		windowAssignment.assignWindowToWorkspace(window:id(), currentWorkspaceNumber)
		windowLayout.showWindowOnScreen(window)
	end
	local focusedWindow = hs.window.focusedWindow()
	if focusedWindow then
		windowAssignment.rememberFocusedWindow(currentWorkspaceNumber, focusedWindow:id())
	end
	renderMenuBarIndicator()
	persistWorkspaceState()
end

function workspaceGrid.currentWorkspaceWindowList()
	local focused = hs.window.focusedWindow()
	return {
		focused = focused and focused:id() or nil,
		windows = windowQuery.windowDescriptorsOnWorkspace(currentWorkspaceNumber),
	}
end

function workspaceGrid.focusWindowById(windowId)
	local window = hs.window.get(windowId)
	if window then
		windowAssignment.assignWindowToWorkspace(windowId, currentWorkspaceNumber)
		window:focus()
		windowLayout.showWindowOnScreen(window)
		persistWorkspaceState()
	end
end

function workspaceGrid.onWindowCreated(window)
	if window and window:id() then
		windowAssignment.assignWindowToWorkspace(window:id(), currentWorkspaceNumber)
		if windowLayout.windowIsTileable(window) then
			windowLayout.showWindowOnScreen(window)
		end
		renderMenuBarIndicator()
		persistWorkspaceState()
	end
end

function workspaceGrid.onWindowDestroyed(window)
	if window and window:id() then
		windowAssignment.forgetWindow(window:id())
		renderMenuBarIndicator()
		persistWorkspaceState()
	end
end

function workspaceGrid.onWindowFocused(window)
	if
		window
		and window:id()
		and windowAssignment.workspaceOfWindowId(window:id()) == currentWorkspaceNumber
		and windowLayout.windowIsTileable(window)
	then
		windowAssignment.rememberFocusedWindow(currentWorkspaceNumber, window:id())
		windowLayout.showWindowOnScreen(window)
	end
end

function workspaceGrid.registerExistingWindowsOnFirstWorkspace()
	for _, window in ipairs(manageableWindows()) do
		if not windowAssignment.isWindowAssigned(window:id()) then
			windowAssignment.assignWindowToWorkspace(window:id(), firstWorkspaceNumber)
		end
	end
	renderMenuBarIndicator()
end

function workspaceGrid.restorePersistedWorkspaceState()
	local restoredCurrentWorkspaceNumber, restoredSessionGenerationToken, restoredAssignments =
		workspaceGridPersistence.load()
	if restoredSessionGenerationToken ~= nil and restoredSessionGenerationToken ~= sessionGeneration.currentToken() then
		currentWorkspaceNumber = firstWorkspaceNumber
		return
	end
	currentWorkspaceNumber = restoredCurrentWorkspaceNumber or currentWorkspaceNumber
	local liveWindowIdSet = {}
	for _, window in ipairs(manageableWindows()) do
		liveWindowIdSet[window:id()] = true
	end
	windowAssignment.adoptAssignmentsForLiveWindows(restoredAssignments, liveWindowIdSet)
end

function workspaceGrid.currentWorkspaceNumber()
	return currentWorkspaceNumber
end

return workspaceGrid
