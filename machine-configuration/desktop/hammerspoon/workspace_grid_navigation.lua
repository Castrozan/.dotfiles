local workspaceGridNavigation = {}

function workspaceGridNavigation.wrapWorkspaceNumber(currentWorkspaceNumber, deltaWithinGrid, totalWorkspaceCount)
	local target = currentWorkspaceNumber + deltaWithinGrid
	if target < 1 then
		target = totalWorkspaceCount + target
	elseif target > totalWorkspaceCount then
		target = target - totalWorkspaceCount
	end
	return target
end

return workspaceGridNavigation
