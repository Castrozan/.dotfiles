local workspaceGridWindowFocus = {}

local windowAssignment = require("workspace_grid_window_assignment")
local windowLayout = require("workspace_grid_window_layout")
local pinnedWindow = require("workspace_grid_pinned_window")

function workspaceGridWindowFocus.buildWindowFocusEntryPoints(dependencies)
	local entryPoints = {}

	function entryPoints.focusWindowById(windowId)
		local window = hs.window.get(windowId)
		if not window then
			return
		end
		local currentWorkspaceNumber = dependencies.currentWorkspaceNumber()
		if pinnedWindow.windowIsPinned(window) then
			dependencies.switchToWorkspace(
				pinnedWindow.resolveWorkspaceForWindow(window, currentWorkspaceNumber),
				window
			)
			return
		end
		windowAssignment.assignWindowToWorkspace(windowId, currentWorkspaceNumber)
		window:focus()
		windowLayout.showWindowOnScreen(window)
		dependencies.persistWorkspaceState()
	end

	function entryPoints.revealWindowById(windowId)
		local window = hs.window.get(windowId)
		if not window then
			return
		end
		local homeWorkspaceNumber =
			pinnedWindow.resolveWorkspaceForWindow(window, windowAssignment.workspaceOfWindowId(windowId))
		if homeWorkspaceNumber == dependencies.currentWorkspaceNumber() then
			entryPoints.focusWindowById(windowId)
			return
		end
		dependencies.switchToWorkspace(homeWorkspaceNumber, window)
	end

	return entryPoints
end

return workspaceGridWindowFocus
