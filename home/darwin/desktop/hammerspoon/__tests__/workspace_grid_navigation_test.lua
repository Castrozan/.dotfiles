local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local navigation = require("workspace_grid_navigation")

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print(string.format("PASS: %s", description))
	end
end

local totalWorkspaceCount = 21

expectEqual(
	"stepping right within the grid stays linear",
	12,
	navigation.wrapWorkspaceNumber(11, 1, totalWorkspaceCount)
)
expectEqual(
	"stepping left within the grid stays linear",
	10,
	navigation.wrapWorkspaceNumber(11, -1, totalWorkspaceCount)
)
expectEqual(
	"stepping past the last workspace wraps to the front",
	1,
	navigation.wrapWorkspaceNumber(21, 1, totalWorkspaceCount)
)
expectEqual(
	"stepping before the first workspace wraps to the back",
	21,
	navigation.wrapWorkspaceNumber(1, -1, totalWorkspaceCount)
)
expectEqual(
	"a full-row jump down past the end wraps around",
	2,
	navigation.wrapWorkspaceNumber(16, 7, totalWorkspaceCount)
)
expectEqual(
	"a full-row jump up before the start wraps around",
	19,
	navigation.wrapWorkspaceNumber(5, -7, totalWorkspaceCount)
)

os.exit(failureCount == 0 and 0 or 1)
