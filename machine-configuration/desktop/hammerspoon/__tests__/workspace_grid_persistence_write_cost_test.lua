local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local realProcessSpawn = os.execute
local processSpawnCallCount = 0
os.execute = function(commandLine)
	processSpawnCallCount = processSpawnCallCount + 1
	return realProcessSpawn(commandLine)
end

hs.fs = {
	mkdir = function(directoryPath)
		return realProcessSpawn("mkdir '" .. directoryPath .. "' 2>/dev/null")
	end,
}

local persistence = require("workspace_grid_persistence")
local warmStateFilePath = os.tmpname()
persistence.setStateFilePathForTest(warmStateFilePath)

persistence.save(7, "boot-token-stable", { [501] = 7, [502] = 3 })
processSpawnCallCount = 0
for _ = 1, 20 do
	persistence.save(7, "boot-token-stable", { [501] = 7, [502] = 3 })
end

expectEqual(
	"a save into an existing directory spawns no process (a shelled-out mkdir -p costs 19ms on rin,"
		.. " and every workspace switch, window create, window destroy and Cmd+Tab commit saves)",
	0,
	processSpawnCallCount
)

local restoredWorkspaceNumber, restoredToken, restoredAssignments = persistence.load()
expectEqual("the warm save still records the active workspace", 7, restoredWorkspaceNumber)
expectEqual("the warm save still records the session generation token", "boot-token-stable", restoredToken)
expectEqual("the warm save still records every window assignment", 3, restoredAssignments[502])

local coldDirectoryRoot = os.tmpname()
os.remove(coldDirectoryRoot)
local coldStateFilePath = coldDirectoryRoot .. "/nested/deeper/workspace-grid-state"
persistence.setStateFilePathForTest(coldStateFilePath)

processSpawnCallCount = 0
persistence.save(4, "boot-token-cold", { [601] = 4 })

expectEqual("a save into a missing directory still spawns no process", 0, processSpawnCallCount)

local coldWorkspaceNumber, _, coldAssignments = persistence.load()
expectEqual("the cold save created the directory chain and wrote the active workspace", 4, coldWorkspaceNumber)
expectEqual("the cold save wrote the window assignments too", 4, coldAssignments[601])

os.execute = realProcessSpawn
os.remove(warmStateFilePath)
os.remove(coldStateFilePath)

harness.exitWithAccumulatedStatus()
