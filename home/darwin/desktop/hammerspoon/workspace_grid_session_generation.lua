local workspaceGridSessionGeneration = {}

local sessionGenerationTokenOverrideForTest = nil

function workspaceGridSessionGeneration.setTokenForTest(token)
	sessionGenerationTokenOverrideForTest = token
end

function workspaceGridSessionGeneration.currentToken()
	if sessionGenerationTokenOverrideForTest ~= nil then
		return sessionGenerationTokenOverrideForTest
	end
	if type(hs) == "table" and type(hs.execute) == "function" then
		local commandOutput = hs.execute("sysctl -n kern.bootsessionuuid")
		local bootSessionUuid = commandOutput and commandOutput:match("[%x%-]+")
		if bootSessionUuid then
			return bootSessionUuid
		end
	end
	return "unknown-boot-session"
end

return workspaceGridSessionGeneration
