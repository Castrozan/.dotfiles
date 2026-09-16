local summonTestHarness = {}

local failureCount = 0

function summonTestHarness.expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print(string.format("PASS: %s", description))
	end
end

function summonTestHarness.timesShellCommandExecuted(executedShellCommands, commandText)
	local occurrences = 0
	for _, executedCommand in ipairs(executedShellCommands) do
		if executedCommand == commandText then
			occurrences = occurrences + 1
		end
	end
	return occurrences
end

function summonTestHarness.exitWithAccumulatedResult()
	os.exit(failureCount == 0 and 0 or 1)
end

return summonTestHarness
