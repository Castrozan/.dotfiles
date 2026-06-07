local workspaceGrid = {}

local workspaceGridColumns = 7
local workspaceGridRows = 3
local totalWorkspaceCount = workspaceGridColumns * workspaceGridRows
local firstWorkspaceNumber = 1

workspaceGrid.columns = workspaceGridColumns
workspaceGrid.totalWorkspaceCount = totalWorkspaceCount

local workspaceNumberByWindowId = {}
local lastFocusedWindowIdByWorkspaceNumber = {}
local currentWorkspaceNumber = firstWorkspaceNumber
local menuBarIndicator = require("workspace_grid_menubar")
local workspaceGridPersistence = require("workspace_grid_persistence")
local windowLayout = require("workspace_grid_window_layout")

local function manageableWindows()
	return hs.window.filter.default:getWindows()
end

local function workspaceOfWindow(window)
	local windowId = window:id()
	if workspaceNumberByWindowId[windowId] == nil then
		workspaceNumberByWindowId[windowId] = firstWorkspaceNumber
	end
	return workspaceNumberByWindowId[windowId]
end

local function occupiedWorkspaceNumbers()
	local occupied = {}
	for _, window in ipairs(manageableWindows()) do
		occupied[workspaceOfWindow(window)] = true
	end
	return occupied
end

local function renderMenuBarIndicator()
	menuBarIndicator.render(currentWorkspaceNumber, workspaceGridColumns, occupiedWorkspaceNumbers())
end

function workspaceGrid.switchToWorkspace(targetWorkspaceNumber, preferredFocusWindow)
	if targetWorkspaceNumber < 1 or targetWorkspaceNumber > totalWorkspaceCount then
		return
	end
	currentWorkspaceNumber = targetWorkspaceNumber
	local rememberedFocusWindowId = lastFocusedWindowIdByWorkspaceNumber[targetWorkspaceNumber]
	local rememberedFocusWindow = nil
	local firstTileableWindow = nil
	for _, window in ipairs(manageableWindows()) do
		if workspaceOfWindow(window) == targetWorkspaceNumber then
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
		lastFocusedWindowIdByWorkspaceNumber[targetWorkspaceNumber] = windowToRefocus:id()
	end
	renderMenuBarIndicator()
	workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
end

function workspaceGrid.moveFocusedWindowToWorkspace(targetWorkspaceNumber)
	local focused = hs.window.focusedWindow()
	if not focused then
		return
	end
	workspaceNumberByWindowId[focused:id()] = targetWorkspaceNumber
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

local function firstStandardWindowForBundleIdentifier(applicationBundleIdentifier)
	for _, application in ipairs(hs.application.applicationsForBundleID(applicationBundleIdentifier)) do
		local mainWindow = application:mainWindow()
		if mainWindow and mainWindow:isStandard() then
			return mainWindow
		end
		for _, window in ipairs(application:allWindows()) do
			if window:isStandard() then
				return window
			end
		end
	end
	return nil
end

function workspaceGrid.summonApplicationToCurrentWorkspace(applicationName, applicationBundleIdentifier)
	local window = firstStandardWindowForBundleIdentifier(applicationBundleIdentifier)
	if not window then
		hs.application.launchOrFocus(applicationName)
		return
	end
	workspaceNumberByWindowId[window:id()] = currentWorkspaceNumber
	windowLayout.showWindowOnScreen(window)
	window:focus()
	renderMenuBarIndicator()
	workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
end

function workspaceGrid.currentWorkspaceWindowList()
	local windows = {}
	for _, window in ipairs(manageableWindows()) do
		if workspaceOfWindow(window) == currentWorkspaceNumber then
			local application = window:application()
			table.insert(windows, {
				["window-id"] = window:id(),
				["app-name"] = (application and application:name()) or "",
				["window-title"] = window:title() or "",
			})
		end
	end
	local focused = hs.window.focusedWindow()
	return {
		focused = focused and focused:id() or nil,
		windows = windows,
	}
end

function workspaceGrid.focusWindowById(windowId)
	local window = hs.window.get(windowId)
	if window then
		workspaceNumberByWindowId[windowId] = currentWorkspaceNumber
		window:focus()
		windowLayout.showWindowOnScreen(window)
		workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
	end
end

function workspaceGrid.onWindowCreated(window)
	if window and window:id() then
		workspaceNumberByWindowId[window:id()] = currentWorkspaceNumber
		if windowLayout.windowIsTileable(window) then
			windowLayout.showWindowOnScreen(window)
		end
		renderMenuBarIndicator()
		workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
	end
end

function workspaceGrid.onWindowFocused(window)
	if
		window
		and window:id()
		and workspaceOfWindow(window) == currentWorkspaceNumber
		and windowLayout.windowIsTileable(window)
	then
		lastFocusedWindowIdByWorkspaceNumber[currentWorkspaceNumber] = window:id()
		windowLayout.showWindowOnScreen(window)
	end
end

function workspaceGrid.registerExistingWindowsOnFirstWorkspace()
	for _, window in ipairs(manageableWindows()) do
		if workspaceNumberByWindowId[window:id()] == nil then
			workspaceNumberByWindowId[window:id()] = firstWorkspaceNumber
		end
	end
	renderMenuBarIndicator()
end

function workspaceGrid.restorePersistedWorkspaceState()
	local restoredCurrentWorkspaceNumber, restoredAssignments = workspaceGridPersistence.load()
	currentWorkspaceNumber = restoredCurrentWorkspaceNumber or currentWorkspaceNumber
	for windowId, workspaceNumber in pairs(restoredAssignments) do
		workspaceNumberByWindowId[windowId] = workspaceNumber
	end
end

function workspaceGrid.currentWorkspaceNumber()
	return currentWorkspaceNumber
end

return workspaceGrid
