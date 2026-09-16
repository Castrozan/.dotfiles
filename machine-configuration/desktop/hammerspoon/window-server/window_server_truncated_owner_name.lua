local windowServerTruncatedOwnerName = {}

local ownerNameCharacterLimit = 31

function windowServerTruncatedOwnerName.asTheWindowServerReportsIt(processName)
	return processName:sub(1, ownerNameCharacterLimit)
end

function windowServerTruncatedOwnerName.identifiesProcessNamed(ownerName, processName)
	if type(ownerName) ~= "string" or ownerName == "" then
		return false
	end
	return ownerName == processName
		or ownerName == windowServerTruncatedOwnerName.asTheWindowServerReportsIt(processName)
end

return windowServerTruncatedOwnerName
