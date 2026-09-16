local workspaceGridWindowSnapshot = {}

local windowQuery = require("workspace_grid_window_query")

local mostRecentlyCapturedSnapshot = { descriptorsByWorkspaceNumber = {}, focusedWindowId = nil }

function workspaceGridWindowSnapshot.captureSnapshot()
	local focusedWindow = hs.window.focusedWindow()
	mostRecentlyCapturedSnapshot = {
		descriptorsByWorkspaceNumber = windowQuery.windowDescriptorsByWorkspace(),
		focusedWindowId = focusedWindow and focusedWindow:id() or nil,
	}
	return mostRecentlyCapturedSnapshot
end

function workspaceGridWindowSnapshot.windowListForWorkspace(workspaceNumber)
	local capturedSnapshot = workspaceGridWindowSnapshot.captureSnapshot()
	local windowsOnWorkspace = {}
	for _, windowDescriptor in ipairs(capturedSnapshot.descriptorsByWorkspaceNumber[workspaceNumber] or {}) do
		table.insert(windowsOnWorkspace, {
			["window-id"] = windowDescriptor["window-id"],
			["app-name"] = windowDescriptor["app-name"],
			["window-title"] = windowDescriptor["window-title"],
		})
	end
	return {
		focused = capturedSnapshot.focusedWindowId,
		windows = windowsOnWorkspace,
	}
end

function workspaceGridWindowSnapshot.snapshotForImmediateUse()
	if next(mostRecentlyCapturedSnapshot.descriptorsByWorkspaceNumber) == nil then
		return workspaceGridWindowSnapshot.captureSnapshot()
	end
	return mostRecentlyCapturedSnapshot
end

return workspaceGridWindowSnapshot
