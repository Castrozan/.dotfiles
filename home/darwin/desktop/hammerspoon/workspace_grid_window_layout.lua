local workspaceGridWindowLayout = {}

local pinnedWindow = require("workspace_grid_pinned_window")

local offScreenParkingX = -1000000
local offScreenParkingDetectionThresholdX = offScreenParkingX / 2
local savedFloatingFrameByWindowId = {}

function workspaceGridWindowLayout.windowIsTileable(window)
	return window:isStandard()
end

function workspaceGridWindowLayout.windowIsParkedOffScreen(window)
	return window:frame().x <= offScreenParkingDetectionThresholdX
end

function workspaceGridWindowLayout.parkWindowOffScreen(window)
	if not workspaceGridWindowLayout.windowIsTileable(window) and savedFloatingFrameByWindowId[window:id()] == nil then
		savedFloatingFrameByWindowId[window:id()] = window:frame()
	end
	local frame = window:frame()
	frame.x = offScreenParkingX
	window:setFrame(frame)
end

function workspaceGridWindowLayout.showWindowOnScreen(window)
	if workspaceGridWindowLayout.windowIsTileable(window) then
		if pinnedWindow.windowIsPinned(window) then
			window:setFrame(window:screen():fullFrame())
		else
			window:setFrame(window:screen():frame())
		end
	else
		local savedFrame = savedFloatingFrameByWindowId[window:id()]
		if savedFrame then
			window:setFrame(savedFrame)
			savedFloatingFrameByWindowId[window:id()] = nil
		end
	end
end

return workspaceGridWindowLayout
