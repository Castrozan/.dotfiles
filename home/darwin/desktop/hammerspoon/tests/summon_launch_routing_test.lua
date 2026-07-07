local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local testDoubles = require("tests.summon_application_test_doubles")
testDoubles.installGlobalHammerspoonMock()

local harness = require("tests.summon_test_harness")
local expectEqual = harness.expectEqual
local timesShellCommandExecuted = harness.timesShellCommandExecuted

local makeFakeWindow = testDoubles.makeFakeWindow
local makeFakeApplication = testDoubles.makeFakeApplication
local setRunningApplications = testDoubles.setRunningApplications
local captures = testDoubles.captures

local workspaceGrid = require("workspace_grid")

local runningBrowserWindow = makeFakeWindow(1, true)
setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({ runningBrowserWindow }) },
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
captures.currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual(
	"a running browser with a window is not relaunched (no reopen, no extra window)",
	0,
	captures.launchOrFocusCallCount
)
expectEqual("a running browser with a window is never quit", 0, captures.killCallCount)
expectEqual("the existing browser window is focused", 1, captures.currentlyFocusedWindowId)
expectEqual("the existing browser window is un-parked onto the screen", 0, runningBrowserWindow.storedFrame.x)

local nonStandardOnlyWindow = makeFakeWindow(9, false)
setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({ nonStandardOnlyWindow }) },
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual("an instance that still owns a non-standard window is never quit", 0, captures.killCallCount)
expectEqual(
	"an instance with only a non-standard window is reactivated via launchOrFocus, not restored",
	1,
	captures.launchOrFocusCallCount
)

setRunningApplications({})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
captures.lastLaunchedApplicationName = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual("a not-running application is cold-launched without any quit", 0, captures.killCallCount)
expectEqual("the not-running cold launch uses launchOrFocus", 1, captures.launchOrFocusCallCount)
expectEqual("the cold launch targets the named application", "Brave Browser", captures.lastLaunchedApplicationName)

setRunningApplications({
	["com.google.Chrome"] = { makeFakeApplication({}) },
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
captures.lastExecuteRanInUserEnvironment = nil
captures.executedShellCommands = {}
workspaceGrid.summonApplicationToCurrentWorkspace("Google Chrome", "com.google.Chrome", "summon-chrome-global")

expectEqual(
	"a windowless instance with a cold-launch command opens chrome-global instead of launchOrFocus",
	1,
	timesShellCommandExecuted(captures.executedShellCommands, "summon-chrome-global")
)
expectEqual(
	"the cold launch runs in the login-shell environment so the nix-profile launcher resolves on PATH",
	true,
	captures.lastExecuteRanInUserEnvironment
)
expectEqual("a cold-launch command suppresses the launchOrFocus fallback", 0, captures.launchOrFocusCallCount)
expectEqual("a cold-launch command never quits the running instance", 0, captures.killCallCount)

local windowedInstanceWindow = makeFakeWindow(2, true)
setRunningApplications({
	["com.google.Chrome"] = {
		makeFakeApplication({}),
		makeFakeApplication({ windowedInstanceWindow }),
	},
})
captures.launchOrFocusCallCount = 0
captures.killCallCount = 0
captures.executedShellCommands = {}
captures.currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Google Chrome", "com.google.Chrome", "summon-chrome-global")

expectEqual(
	"a windowed instance is focused even when a windowless instance also runs",
	2,
	captures.currentlyFocusedWindowId
)
expectEqual("no launch happens when any instance already has a window", 0, captures.launchOrFocusCallCount)
expectEqual(
	"an existing window short-circuits the cold launch even with a command present",
	0,
	timesShellCommandExecuted(captures.executedShellCommands, "summon-chrome-global")
)

harness.exitWithAccumulatedResult()
