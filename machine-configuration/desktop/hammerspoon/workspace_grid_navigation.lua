local workspaceGridNavigation = {}

local pinnedWindow = require("workspace_grid_pinned_window")
local windowAssignment = require("workspace_grid_window_assignment")

function workspaceGridNavigation.wrapWorkspaceNumber(currentWorkspaceNumber, deltaWithinGrid, totalWorkspaceCount)
	local target = currentWorkspaceNumber + deltaWithinGrid
	if target < 1 then
		target = totalWorkspaceCount + target
	elseif target > totalWorkspaceCount then
		target = target - totalWorkspaceCount
	end
	return target
end

function workspaceGridNavigation.buildNavigationEntryPoints(dependencies)
	local entryPoints = {}

	function entryPoints.moveFocusedWindowToWorkspace(targetWorkspaceNumber)
		local focusedWindow = hs.window.focusedWindow()
		if not focusedWindow then
			return
		end
		if pinnedWindow.windowIsPinned(focusedWindow) then
			dependencies.switchToWorkspace(targetWorkspaceNumber)
			return
		end
		windowAssignment.assignWindowToWorkspace(focusedWindow:id(), targetWorkspaceNumber)
		dependencies.switchToWorkspace(targetWorkspaceNumber, focusedWindow)
	end

	function entryPoints.navigateWorkspace(deltaWithinGrid, alsoMoveFocusedWindow)
		local targetWorkspaceNumber = workspaceGridNavigation.wrapWorkspaceNumber(
			dependencies.currentWorkspaceNumber(),
			deltaWithinGrid,
			dependencies.totalWorkspaceCount
		)
		if alsoMoveFocusedWindow then
			entryPoints.moveFocusedWindowToWorkspace(targetWorkspaceNumber)
		else
			dependencies.switchToWorkspace(targetWorkspaceNumber)
		end
	end

	return entryPoints
end

return workspaceGridNavigation
