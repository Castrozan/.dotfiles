local workspaceGridWindowEvents = {}

local pinnedWindow = require("workspace_grid_pinned_window")
local windowAssignment = require("workspace_grid_window_assignment")
local windowLayout = require("workspace_grid_window_layout")
local windowQuery = require("workspace_grid_window_query")

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
			windowLayout.showWindowOnScreen(window)
		end
		context.renderMenuBarIndicator()
		context.persistWorkspaceState()
	end

	handlers.onWindowCreated = adoptWindowOntoCurrentWorkspace
	handlers.onWindowLeftFullScreen = adoptWindowOntoCurrentWorkspace

	function handlers.onWindowDestroyed(window)
		if window and window:id() and windowQuery.windowIsNoLongerManageable(window:id()) then
			windowAssignment.forgetWindow(window:id())
			context.renderMenuBarIndicator()
			context.persistWorkspaceState()
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
			if windowLayout.windowIsParkedOffScreen(window) then
				windowLayout.showWindowOnScreen(window)
			end
		end
	end

	return handlers
end

return workspaceGridWindowEvents
