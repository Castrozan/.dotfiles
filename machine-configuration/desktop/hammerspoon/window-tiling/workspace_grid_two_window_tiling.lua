local workspaceGridTwoWindowTiling = {}

local windowLayout = require("workspace_grid_window_layout")

local activePair = nil
local instantFrameTransitionSeconds = 0

local function frameHalves(screenFrame)
	local leftWidth = math.floor(screenFrame.w / 2)
	return {
		x = screenFrame.x,
		y = screenFrame.y,
		w = leftWidth,
		h = screenFrame.h,
	}, {
		x = screenFrame.x + leftWidth,
		y = screenFrame.y,
		w = screenFrame.w - leftWidth,
		h = screenFrame.h,
	}
end

local function restoreWindowUnlessDestroyed(window, destroyedWindowId)
	if window:id() ~= destroyedWindowId then
		windowLayout.showWindowOnScreen(window)
	end
end

function workspaceGridTwoWindowTiling.activate(leftWindow, rightWindow)
	if activePair ~= nil or leftWindow == nil or rightWindow == nil or leftWindow:id() == rightWindow:id() then
		return false
	end
	local screen = leftWindow:screen()
	if screen == nil then
		return false
	end
	local leftFrame, rightFrame = frameHalves(screen:frame())
	leftWindow:setFrame(leftFrame, instantFrameTransitionSeconds)
	rightWindow:setFrame(rightFrame, instantFrameTransitionSeconds)
	activePair = {
		leftWindow = leftWindow,
		rightWindow = rightWindow,
	}
	return true
end

function workspaceGridTwoWindowTiling.deactivate(destroyedWindowId)
	if activePair == nil then
		return false
	end
	local pairToRestore = activePair
	activePair = nil
	restoreWindowUnlessDestroyed(pairToRestore.leftWindow, destroyedWindowId)
	restoreWindowUnlessDestroyed(pairToRestore.rightWindow, destroyedWindowId)
	return true
end

function workspaceGridTwoWindowTiling.isActive()
	return activePair ~= nil
end

function workspaceGridTwoWindowTiling.containsWindow(window)
	if activePair == nil or window == nil or window:id() == nil then
		return false
	end
	local windowId = window:id()
	return activePair.leftWindow:id() == windowId or activePair.rightWindow:id() == windowId
end

function workspaceGridTwoWindowTiling.focusLeftWindow()
	if activePair == nil then
		return false
	end
	activePair.leftWindow:focus()
	return true
end

function workspaceGridTwoWindowTiling.focusRightWindow()
	if activePair == nil then
		return false
	end
	activePair.rightWindow:focus()
	return true
end

return workspaceGridTwoWindowTiling
