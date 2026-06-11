local workspaceGridWindowQuery = {}

local windowAssignment = require("workspace_grid_window_assignment")

function workspaceGridWindowQuery.liveWindowIdSet()
	local liveWindowIds = {}
	for _, window in ipairs(hs.window.allWindows()) do
		liveWindowIds[window:id()] = true
	end
	return liveWindowIds
end

function workspaceGridWindowQuery.manageableWindows()
	local liveWindowIds = workspaceGridWindowQuery.liveWindowIdSet()
	local liveWindows = {}
	for _, window in ipairs(hs.window.filter.default:getWindows()) do
		if liveWindowIds[window:id()] then
			liveWindows[#liveWindows + 1] = window
		end
	end
	return liveWindows
end

function workspaceGridWindowQuery.occupiedWorkspaceNumbers()
	local occupied = {}
	for _, window in ipairs(workspaceGridWindowQuery.manageableWindows()) do
		occupied[windowAssignment.workspaceOfWindowId(window:id())] = true
	end
	return occupied
end

function workspaceGridWindowQuery.windowDescriptorsOnWorkspace(workspaceNumber)
	local windowDescriptors = {}
	for _, window in ipairs(workspaceGridWindowQuery.manageableWindows()) do
		if windowAssignment.workspaceOfWindowId(window:id()) == workspaceNumber then
			local application = window:application()
			table.insert(windowDescriptors, {
				["window-id"] = window:id(),
				["app-name"] = (application and application:name()) or "",
				["window-title"] = window:title() or "",
			})
		end
	end
	return windowDescriptors
end

return workspaceGridWindowQuery
