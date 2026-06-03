-- Virtual-workspace window manager replicating the AeroSpace 7x3 grid by
-- show/hiding windows on one macOS Space (Hammerspoon is notarized so Sophos
-- does not block it). Standard windows on the active workspace are maximized
-- (accordion); dialogs/panels float and restore to position on switch. The
-- Cmd+Tab switcher is the separate Swift daemon, fed by switcher_bridge.lua.

local workspaceGrid = {}

local workspaceGridColumns = 7
local workspaceGridRows = 3
local totalWorkspaceCount = workspaceGridColumns * workspaceGridRows
local offScreenParkingX = -1000000
local firstWorkspaceNumber = 1

workspaceGrid.columns = workspaceGridColumns
workspaceGrid.totalWorkspaceCount = totalWorkspaceCount

local workspaceNumberByWindowId = {}
local savedFloatingFrameByWindowId = {}
local currentWorkspaceNumber = firstWorkspaceNumber
local menuBarIndicator = require("workspace_grid_menubar")
local workspaceGridPersistence = require("workspace_grid_persistence")

local function manageableWindows()
	return hs.window.filter.default:getWindows()
end

-- Dialogs/panels float at their natural size instead of being maximized.
local function windowIsTileable(window)
	return window:isStandard()
end

local function workspaceOfWindow(window)
	local windowId = window:id()
	if workspaceNumberByWindowId[windowId] == nil then
		-- Default unknown windows to ws 1, never to the switch target (else switching
		-- to an empty workspace would claim every unassigned window).
		workspaceNumberByWindowId[windowId] = firstWorkspaceNumber
	end
	return workspaceNumberByWindowId[windowId]
end

local function parkWindowOffScreen(window)
	if not windowIsTileable(window) and savedFloatingFrameByWindowId[window:id()] == nil then
		savedFloatingFrameByWindowId[window:id()] = window:frame()
	end
	local frame = window:frame()
	frame.x = offScreenParkingX
	window:setFrame(frame)
end

local function showWindowOnScreen(window)
	if windowIsTileable(window) then
		window:setFrame(window:screen():frame())
	else
		local savedFrame = savedFloatingFrameByWindowId[window:id()]
		if savedFrame then
			window:setFrame(savedFrame)
			savedFloatingFrameByWindowId[window:id()] = nil
		end
	end
end

function workspaceGrid.switchToWorkspace(targetWorkspaceNumber, preferredFocusWindow)
	if targetWorkspaceNumber < 1 or targetWorkspaceNumber > totalWorkspaceCount then
		return
	end
	currentWorkspaceNumber = targetWorkspaceNumber
	local windowToRefocus = nil
	for _, window in ipairs(manageableWindows()) do
		if workspaceOfWindow(window) == targetWorkspaceNumber then
			showWindowOnScreen(window)
			if windowIsTileable(window) then
				windowToRefocus = window
			end
		else
			parkWindowOffScreen(window)
		end
	end
	if preferredFocusWindow then
		windowToRefocus = preferredFocusWindow
	end
	if windowToRefocus then
		windowToRefocus:focus()
	end
	menuBarIndicator.render(currentWorkspaceNumber, totalWorkspaceCount)
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

function workspaceGrid.summonApplicationToCurrentWorkspace(applicationName)
	local application = hs.application.get(applicationName)
	if not application then
		hs.application.launchOrFocus(applicationName)
		application = hs.application.get(applicationName)
	end
	if not application then
		return
	end
	local window = application:mainWindow() or application:allWindows()[1]
	if window then
		workspaceNumberByWindowId[window:id()] = currentWorkspaceNumber
		showWindowOnScreen(window)
		window:focus()
		workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
	end
end

-- Consumed by switcher_bridge.lua to feed the Swift Cmd+Tab daemon the active
-- workspace's windows, in the shape its WorkspaceWindow decoder expects.
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
		showWindowOnScreen(window)
		workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
	end
end

function workspaceGrid.onWindowCreated(window)
	if window and window:id() then
		workspaceNumberByWindowId[window:id()] = currentWorkspaceNumber
		if windowIsTileable(window) then
			showWindowOnScreen(window)
		end
		workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
	end
end

function workspaceGrid.onWindowFocused(window)
	if window and window:id() and workspaceOfWindow(window) == currentWorkspaceNumber and windowIsTileable(window) then
		showWindowOnScreen(window)
	end
end

function workspaceGrid.registerExistingWindowsOnFirstWorkspace()
	for _, window in ipairs(manageableWindows()) do
		if workspaceNumberByWindowId[window:id()] == nil then
			workspaceNumberByWindowId[window:id()] = firstWorkspaceNumber
		end
	end
	menuBarIndicator.render(currentWorkspaceNumber, totalWorkspaceCount)
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
