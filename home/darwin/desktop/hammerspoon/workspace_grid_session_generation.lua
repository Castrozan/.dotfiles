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
		local commandOutput = hs.execute("sysctl -n kern.boottime")
		local bootEpochSeconds = commandOutput and commandOutput:match("sec%s*=%s*(%d+)")
		if bootEpochSeconds then
			return bootEpochSeconds
		end
	end
	return "unknown-boot"
end

return workspaceGridSessionGeneration
