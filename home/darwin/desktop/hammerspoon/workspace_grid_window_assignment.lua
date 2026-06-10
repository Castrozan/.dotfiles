local workspaceGridWindowAssignment = {}

local defaultWorkspaceNumber = 1
local workspaceNumberByWindowId = {}
local lastFocusedWindowIdByWorkspaceNumber = {}

function workspaceGridWindowAssignment.workspaceOfWindowId(windowId)
	if workspaceNumberByWindowId[windowId] == nil then
		workspaceNumberByWindowId[windowId] = defaultWorkspaceNumber
	end
	return workspaceNumberByWindowId[windowId]
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

function workspaceGridWindowAssignment.adoptAssignmentsForLiveWindows(restoredAssignments, liveWindowIdSet)
	for windowId, workspaceNumber in pairs(restoredAssignments) do
		if liveWindowIdSet[windowId] then
			workspaceNumberByWindowId[windowId] = workspaceNumber
		end
	end
end

function workspaceGridWindowAssignment.forgetWindowsFailingLivenessCheck(windowIsLive)
	local staleWindowIds = {}
	for windowId in pairs(workspaceNumberByWindowId) do
		if not windowIsLive(windowId) then
			staleWindowIds[#staleWindowIds + 1] = windowId
		end
	end
	for _, windowId in ipairs(staleWindowIds) do
		workspaceGridWindowAssignment.forgetWindow(windowId)
	end
end

return workspaceGridWindowAssignment
