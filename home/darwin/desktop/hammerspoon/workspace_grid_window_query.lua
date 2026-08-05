local workspaceGridWindowQuery = {}

local windowAssignment = require("workspace_grid_window_assignment")

local includeWindowsBelowTheDock = false

function workspaceGridWindowQuery.liveWindowIdSet()
	local liveWindowIds = {}
	for _, windowServerEntry in ipairs(hs.window.list(includeWindowsBelowTheDock)) do
		liveWindowIds[windowServerEntry.kCGWindowNumber] = true
	end
	return liveWindowIds
end

function workspaceGridWindowQuery.windowServerConfirmsWindowIsGone(windowId)
	local liveWindowIds = workspaceGridWindowQuery.liveWindowIdSet()
	if next(liveWindowIds) == nil then
		return false
	end
	return liveWindowIds[windowId] ~= true
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

function workspaceGridWindowQuery.manageableWindowById(windowId)
	for _, window in ipairs(workspaceGridWindowQuery.manageableWindows()) do
		if window:id() == windowId then
			return window
		end
	end
	return nil
end

function workspaceGridWindowQuery.occupiedWorkspaceNumbers()
	local occupied = {}
	for _, window in ipairs(workspaceGridWindowQuery.manageableWindows()) do
		occupied[windowAssignment.workspaceOfWindowId(window:id())] = true
	end
	return occupied
end

function workspaceGridWindowQuery.windowDescriptorsByWorkspace()
	local windowDescriptorsByWorkspaceNumber = {}
	for _, window in ipairs(workspaceGridWindowQuery.manageableWindows()) do
		local workspaceNumber = windowAssignment.workspaceOfWindowId(window:id())
		local windowDescriptorsOnWorkspace = windowDescriptorsByWorkspaceNumber[workspaceNumber]
		if windowDescriptorsOnWorkspace == nil then
			windowDescriptorsOnWorkspace = {}
			windowDescriptorsByWorkspaceNumber[workspaceNumber] = windowDescriptorsOnWorkspace
		end
		local application = window:application()
		table.insert(windowDescriptorsOnWorkspace, {
			["window-id"] = window:id(),
			["app-name"] = (application and application:name()) or "",
			["app-bundle-id"] = (application and application:bundleID()) or "",
			["window-title"] = window:title() or "",
		})
	end
	return windowDescriptorsByWorkspaceNumber
end

return workspaceGridWindowQuery
