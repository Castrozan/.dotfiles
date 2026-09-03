local workspaceGridWindowEvents = {}

local pinnedWindow = require("workspace_grid_pinned_window")
local windowAssignment = require("workspace_grid_window_assignment")
local windowLayout = require("workspace_grid_window_layout")
local windowQuery = require("workspace_grid_window_query")
local twoWindowTiling = require("workspace_grid_two_window_tiling")

function workspaceGridWindowEvents.buildWindowEventHandlers(context)
	local handlers = {}

	local function adoptWindowOntoCurrentWorkspace(window)
		if not (window and window:id()) then
			return
		end
		local assignedWorkspaceNumber = pinnedWindow.resolveWorkspaceForWindow(window, context.currentWorkspaceNumber())
		windowAssignment.assignWindowToWorkspace(window:id(), assignedWorkspaceNumber)
		if assignedWorkspaceNumber ~= context.currentWorkspaceNumber() then
			windowLayout.parkWindowOffScreen(window)
		elseif windowLayout.windowIsTileable(window) then
			twoWindowTiling.deactivate()
			windowLayout.showWindowOnScreen(window)
		end
		context.renderMenuBarIndicator()
		context.onWorkspaceLayoutChanged()
	end

	handlers.onWindowCreated = adoptWindowOntoCurrentWorkspace
	handlers.onWindowLeftFullScreen = adoptWindowOntoCurrentWorkspace

	function handlers.onWindowDestroyed(window)
		if not (window and window:id()) then
			return
		end
		local tilingStateChanged = false
		if twoWindowTiling.containsWindow(window) then
			tilingStateChanged = twoWindowTiling.deactivate(window:id())
		end
		if windowQuery.windowIsNoLongerManageable(window:id()) then
			windowAssignment.forgetWindow(window:id())
			context.renderMenuBarIndicator()
			context.onWorkspaceLayoutChanged()
		elseif tilingStateChanged then
			context.onWorkspaceLayoutChanged()
		end
	end

	function handlers.onWindowFocused(window)
		if
			window
			and window:id()
			and windowAssignment.workspaceOfWindowId(window:id()) == context.currentWorkspaceNumber()
			and windowLayout.windowIsTileable(window)
		then
			windowAssignment.rememberFocusedWindow(context.currentWorkspaceNumber(), window:id())
			local tilingStateChanged = false
			if twoWindowTiling.isActive() and not twoWindowTiling.containsWindow(window) then
				tilingStateChanged = twoWindowTiling.deactivate()
			end
			if windowLayout.windowIsParkedOffScreen(window) then
				windowLayout.showWindowOnScreen(window)
			end
			if tilingStateChanged then
				context.onWorkspaceLayoutChanged()
			end
		end
	end

	return handlers
end

return workspaceGridWindowEvents
