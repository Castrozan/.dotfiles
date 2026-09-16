local workspaceGridTwoWindowTilingEntryPoints = {}

local pinnedWindow = require("workspace_grid_pinned_window")
local windowAssignment = require("workspace_grid_window_assignment")
local windowLayout = require("workspace_grid_window_layout")
local windowQuery = require("workspace_grid_window_query")
local twoWindowTiling = require("workspace_grid_two_window_tiling")

function workspaceGridTwoWindowTilingEntryPoints.install(workspaceGrid, dependencies)
	local entryPoints = {}

	function entryPoints.toggleTwoWindowTiling()
		if twoWindowTiling.isActive() then
			twoWindowTiling.deactivate()
			dependencies.onWorkspaceLayoutChanged()
			return false
		end
		local focusedWindow = hs.window.focusedWindow()
		local currentWorkspaceNumber = dependencies.currentWorkspaceNumber()
		if
			focusedWindow == nil
			or focusedWindow:id() == nil
			or windowAssignment.workspaceOfWindowId(focusedWindow:id()) ~= currentWorkspaceNumber
			or not windowLayout.windowIsTileable(focusedWindow)
			or pinnedWindow.windowIsPinned(focusedWindow)
		then
			return false
		end
		local previousWindowId = windowAssignment.previouslyFocusedWindowId(currentWorkspaceNumber)
		if previousWindowId == nil then
			return false
		end
		local previousWindow = windowQuery.manageableWindowById(previousWindowId)
		if
			previousWindow == nil
			or windowAssignment.workspaceOfWindowId(previousWindowId) ~= currentWorkspaceNumber
			or not windowLayout.windowIsTileable(previousWindow)
			or pinnedWindow.windowIsPinned(previousWindow)
		then
			return false
		end
		if not twoWindowTiling.activate(focusedWindow, previousWindow) then
			return false
		end
		dependencies.onWorkspaceLayoutChanged()
		return true
	end

	function entryPoints.twoWindowTilingIsActive()
		return twoWindowTiling.isActive()
	end

	function entryPoints.focusLeftTiledWindow()
		return twoWindowTiling.focusLeftWindow()
	end

	function entryPoints.focusRightTiledWindow()
		return twoWindowTiling.focusRightWindow()
	end

	workspaceGrid.toggleTwoWindowTiling = entryPoints.toggleTwoWindowTiling
	workspaceGrid.twoWindowTilingIsActive = entryPoints.twoWindowTilingIsActive
	workspaceGrid.focusLeftTiledWindow = entryPoints.focusLeftTiledWindow
	workspaceGrid.focusRightTiledWindow = entryPoints.focusRightTiledWindow
end

return workspaceGridTwoWindowTilingEntryPoints
