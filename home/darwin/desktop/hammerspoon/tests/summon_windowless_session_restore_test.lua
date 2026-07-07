local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local testDoubles = require("tests.summon_application_test_doubles")
testDoubles.installGlobalHammerspoonMock()

local harness = require("tests.summon_test_harness")
local expectEqual = harness.expectEqual

local makeFakeApplication = testDoubles.makeFakeApplication
local setRunningApplications = testDoubles.setRunningApplications
local captures = testDoubles.captures

local workspaceGrid = require("workspace_grid")

setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({}) },
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
captures.lastLaunchedApplicationName = nil
captures.executedShellCommands = {}
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual(
	"a windowless running instance is quit so the relaunch can restore the previous session",
	1,
	captures.killCallCount
)
expectEqual("after the windowless instance terminates it is cold-relaunched", 1, captures.launchOrFocusCallCount)
expectEqual("the relaunch targets the named application", "Brave Browser", captures.lastLaunchedApplicationName)
expectEqual("the session-restore relaunch runs no shell command", 0, #captures.executedShellCommands)

captures.deferTerminationAndRelaunch = true
captures.pendingRelaunchActions = {}
setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({}) },
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual("the first windowless summon quits the instance once", 1, captures.killCallCount)
expectEqual("the relaunch stays pending until the instance actually terminates", 0, captures.launchOrFocusCallCount)

workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual(
	"a second summon during the in-flight relaunch is suppressed by the guard and does not quit again",
	1,
	captures.killCallCount
)

testDoubles.finishPendingTerminations()
testDoubles.runPendingRelaunchActions()

expectEqual(
	"once the instance terminates the guarded relaunch cold-launches exactly once",
	1,
	captures.launchOrFocusCallCount
)

setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({}) },
})
captures.killCallCount = 0
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual("the in-progress guard was cleared, so a later windowless summon quits again", 1, captures.killCallCount)

testDoubles.finishPendingTerminations()
testDoubles.runPendingRelaunchActions()

setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({}) },
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
captures.pendingRelaunchActions = {}
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

local terminationThatNeverCompletesTick = captures.pendingRelaunchActions[1]
for _ = 1, 60 do
	terminationThatNeverCompletesTick()
end

expectEqual(
	"an instance that refuses to terminate is force-relaunched after the poll budget instead of wedging",
	1,
	captures.launchOrFocusCallCount
)

setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({}) },
})
captures.killCallCount = 0
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual("the guard is released after a give-up relaunch, so summons keep working", 1, captures.killCallCount)

testDoubles.finishPendingTerminations()
testDoubles.runPendingRelaunchActions()
captures.deferTerminationAndRelaunch = false
captures.pendingRelaunchActions = {}

harness.exitWithAccumulatedResult()
