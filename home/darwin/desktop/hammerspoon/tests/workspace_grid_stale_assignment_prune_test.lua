-- Verifies stale-assignment pruning: a window id whose window no longer exists
-- must be dropped from the assignment map so it is never re-persisted nor
-- inherited by a recycled id, while live windows keep their workspace.

local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local windowAssignment = require("workspace_grid_window_assignment")

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
  if expectedValue ~= actualValue then
    failureCount = failureCount + 1
    print(string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue)))
  else
    print(string.format("PASS: %s", description))
  end
end

windowAssignment.assignWindowToWorkspace(1, 5)
windowAssignment.assignWindowToWorkspace(99, 10)
windowAssignment.assignWindowToWorkspace(2, 6)

local liveWindowIds = { [1] = true, [2] = true }
windowAssignment.forgetWindowsFailingLivenessCheck(function(windowId)
  return liveWindowIds[windowId] == true
end)

local assignmentsByWindowId = windowAssignment.allWorkspaceNumbersByWindowId()
expectEqual("live window 1 keeps its workspace", 5, assignmentsByWindowId[1])
expectEqual("live window 2 keeps its workspace", 6, assignmentsByWindowId[2])
expectEqual("dead window 99 is pruned from the assignment map", nil, assignmentsByWindowId[99])

os.exit(failureCount == 0 and 0 or 1)
