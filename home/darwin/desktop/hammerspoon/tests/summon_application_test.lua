local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local testDoubles = require("tests.summon_application_test_doubles")
testDoubles.installGlobalHammerspoonMock()

local makeFakeWindow = testDoubles.makeFakeWindow
local makeFakeApplication = testDoubles.makeFakeApplication
local setRunningApplications = testDoubles.setRunningApplications
local captures = testDoubles.captures

local workspaceGrid = require("workspace_grid")

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

local function timesShellCommandExecuted(commandText)
	local occurrences = 0
	for _, executedCommand in ipairs(captures.executedShellCommands) do
		if executedCommand == commandText then
			occurrences = occurrences + 1
		end
	end
	return occurrences
end

local runningBrowserWindow = makeFakeWindow(1, true)
setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({ runningBrowserWindow }) },
})
captures.launchOrFocusCallCount = 0
captures.currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual(
	"a running browser with a window is not relaunched (no reopen, no extra window)",
	0,
	captures.launchOrFocusCallCount
)
expectEqual("the existing browser window is focused", 1, captures.currentlyFocusedWindowId)
expectEqual("the existing browser window is un-parked onto the screen", 0, runningBrowserWindow.storedFrame.x)

setRunningApplications({
	["com.google.Chrome"] = { makeFakeApplication({}) },
})
captures.launchOrFocusCallCount = 0
captures.lastLaunchedApplicationName = nil
captures.lastExecuteRanInUserEnvironment = nil
captures.executedShellCommands = {}
captures.currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Google Chrome", "com.google.Chrome", "summon-chrome-global")

expectEqual(
	"a windowless instance with a cold-launch command opens chrome-global instead of launchOrFocus",
	1,
	timesShellCommandExecuted("summon-chrome-global")
)
expectEqual(
	"the cold launch runs in the login-shell environment so the nix-profile launcher resolves on PATH",
	true,
	captures.lastExecuteRanInUserEnvironment
)
expectEqual("a cold-launch command suppresses the launchOrFocus fallback", 0, captures.launchOrFocusCallCount)

setRunningApplications({
	["com.brave.Browser"] = { makeFakeApplication({}) },
})
captures.launchOrFocusCallCount = 0
captures.lastLaunchedApplicationName = nil
captures.executedShellCommands = {}
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual(
	"a windowless instance without a cold-launch command falls back to launchOrFocus",
	1,
	captures.launchOrFocusCallCount
)
expectEqual("the fallback launch targets the named application", "Brave Browser", captures.lastLaunchedApplicationName)
expectEqual("the fallback path runs no shell command", 0, #captures.executedShellCommands)

local windowedInstanceWindow = makeFakeWindow(2, true)
setRunningApplications({
	["com.google.Chrome"] = {
		makeFakeApplication({}),
		makeFakeApplication({ windowedInstanceWindow }),
	},
})
captures.launchOrFocusCallCount = 0
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
	timesShellCommandExecuted("summon-chrome-global")
)

os.exit(failureCount == 0 and 0 or 1)
