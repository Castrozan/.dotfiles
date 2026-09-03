local workspaceGridWindowAssignment = {}

local defaultWorkspaceNumber = 11
local workspaceNumberByWindowId = {}
local focusedWindowIdsByRecencyByWorkspaceNumber = {}

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
	for workspaceNumber, focusedWindowIdsByRecency in pairs(focusedWindowIdsByRecencyByWorkspaceNumber) do
		for recencyIndex = #focusedWindowIdsByRecency, 1, -1 do
			if focusedWindowIdsByRecency[recencyIndex] == windowId then
				table.remove(focusedWindowIdsByRecency, recencyIndex)
			end
		end
		if #focusedWindowIdsByRecency == 0 then
			focusedWindowIdsByRecencyByWorkspaceNumber[workspaceNumber] = nil
		end
	end
end

function workspaceGridWindowAssignment.rememberFocusedWindow(workspaceNumber, windowId)
	local focusedWindowIdsByRecency = focusedWindowIdsByRecencyByWorkspaceNumber[workspaceNumber] or {}
	for recencyIndex = #focusedWindowIdsByRecency, 1, -1 do
		if focusedWindowIdsByRecency[recencyIndex] == windowId then
			table.remove(focusedWindowIdsByRecency, recencyIndex)
		end
	end
	table.insert(focusedWindowIdsByRecency, 1, windowId)
	while #focusedWindowIdsByRecency > 2 do
		table.remove(focusedWindowIdsByRecency)
	end
	focusedWindowIdsByRecencyByWorkspaceNumber[workspaceNumber] = focusedWindowIdsByRecency
end

function workspaceGridWindowAssignment.rememberedFocusedWindowId(workspaceNumber)
	local focusedWindowIdsByRecency = focusedWindowIdsByRecencyByWorkspaceNumber[workspaceNumber] or {}
	return focusedWindowIdsByRecency[1]
end

function workspaceGridWindowAssignment.previouslyFocusedWindowId(workspaceNumber)
	local focusedWindowIdsByRecency = focusedWindowIdsByRecencyByWorkspaceNumber[workspaceNumber] or {}
	return focusedWindowIdsByRecency[2]
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
