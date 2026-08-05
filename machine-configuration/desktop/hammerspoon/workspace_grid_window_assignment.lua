local workspaceGridWindowAssignment = {}

local defaultWorkspaceNumber = 11
local workspaceNumberByWindowId = {}
local lastFocusedWindowIdByWorkspaceNumber = {}

function workspaceGridWindowAssignment.workspaceOfWindowId(windowId)
	local assignedWorkspaceNumber = workspaceNumberByWindowId[windowId]
	if assignedWorkspaceNumber == nil then
		return defaultWorkspaceNumber
	end
	return assignedWorkspaceNumber
end

function workspaceGridWindowAssignment.assignWindowToWorkspace(windowId, workspaceNumber)
	workspaceNumberByWindowId[windowId] = workspaceNumber
end

function workspaceGridWindowAssignment.isWindowAssigned(windowId)
	return workspaceNumberByWindowId[windowId] ~= nil
end

function workspaceGridWindowAssignment.forgetWindow(windowId)
	workspaceNumberByWindowId[windowId] = nil
	for workspaceNumber, focusedWindowId in pairs(lastFocusedWindowIdByWorkspaceNumber) do
		if focusedWindowId == windowId then
			lastFocusedWindowIdByWorkspaceNumber[workspaceNumber] = nil
		end
	end
end

function workspaceGridWindowAssignment.rememberFocusedWindow(workspaceNumber, windowId)
	lastFocusedWindowIdByWorkspaceNumber[workspaceNumber] = windowId
end

function workspaceGridWindowAssignment.rememberedFocusedWindowId(workspaceNumber)
	return lastFocusedWindowIdByWorkspaceNumber[workspaceNumber]
end

function workspaceGridWindowAssignment.allWorkspaceNumbersByWindowId()
	return workspaceNumberByWindowId
end

function workspaceGridWindowAssignment.adoptPersistedAssignments(restoredAssignments)
	for windowId, workspaceNumber in pairs(restoredAssignments) do
		workspaceNumberByWindowId[windowId] = workspaceNumber
	end
end

return workspaceGridWindowAssignment
