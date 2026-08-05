local workspaceGridWindowQuery = {}

local windowAssignment = require("workspace_grid_window_assignment")
local windowServerOwnerName = require("window_server_truncated_owner_name")

local includeWindowsBelowTheDock = false
local switcherOverlayProcessName = "workspace-window-switcher-daemon"

function workspaceGridWindowQuery.manageableWindowIdSet()
	local manageableWindowIds = {}
	for _, windowServerEntry in ipairs(hs.window.list(includeWindowsBelowTheDock)) do
		local belongsToTheSwitcherOverlay = windowServerOwnerName.identifiesProcessNamed(
			windowServerEntry.kCGWindowOwnerName,
			switcherOverlayProcessName
		)
		if not belongsToTheSwitcherOverlay then
			manageableWindowIds[windowServerEntry.kCGWindowNumber] = true
		end
	end
	return manageableWindowIds
end

function workspaceGridWindowQuery.windowIsNoLongerManageable(windowId)
	local manageableWindowIds = workspaceGridWindowQuery.manageableWindowIdSet()
	if next(manageableWindowIds) == nil then
		return false
	end
	return manageableWindowIds[windowId] ~= true
end

function workspaceGridWindowQuery.manageableWindows()
	local manageableWindowIds = workspaceGridWindowQuery.manageableWindowIdSet()
	local manageableWindows = {}
	for _, window in ipairs(hs.window.filter.default:getWindows()) do
		if manageableWindowIds[window:id()] then
			manageableWindows[#manageableWindows + 1] = window
		end
	end
	return manageableWindows
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
