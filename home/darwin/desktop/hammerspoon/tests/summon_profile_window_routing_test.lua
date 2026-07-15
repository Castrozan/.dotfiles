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
local chromePersonalProfileWindow = require("chrome_personal_profile_window")

local function withTitle(window, title)
	function window:title()
		return title
	end
	return window
end

local function summonPersonalProfile()
	workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace(
		"com.google.Chrome",
		"summon-chrome-personal-profile",
		chromePersonalProfileWindow.windowBelongsToPersonalProfile
	)
end

local workProfileWindow = withTitle(makeFakeWindow(1, true), "Slack - Google Chrome - Lucas (Work)")
local personalProfileWindow = withTitle(makeFakeWindow(2, true), "New Tab - Google Chrome - Lucas")
setRunningApplications({
	["com.google.Chrome"] = { makeFakeApplication({ workProfileWindow, personalProfileWindow }) },
})
captures.currentlyFocusedWindowId = nil
captures.executedShellCommands = {}
summonPersonalProfile()

expectEqual("the personal-profile window is focused, not the work-profile window", 2, captures.currentlyFocusedWindowId)
expectEqual("the personal-profile window is un-parked onto the screen", 0, personalProfileWindow.storedFrame.x)
expectEqual(
	"no cold launch runs when a personal-profile window already exists",
	0,
	timesShellCommandExecuted(captures.executedShellCommands, "summon-chrome-personal-profile")
)

setRunningApplications({
	["com.google.Chrome"] = { makeFakeApplication({ workProfileWindow }) },
})
captures.currentlyFocusedWindowId = nil
captures.executedShellCommands = {}
captures.lastExecuteRanInUserEnvironment = nil
summonPersonalProfile()

expectEqual(
	"a work-profile window does not satisfy the personal-profile summon",
	nil,
	captures.currentlyFocusedWindowId
)
expectEqual(
	"the personal profile is cold-launched when only a work-profile window exists",
	1,
	timesShellCommandExecuted(captures.executedShellCommands, "summon-chrome-personal-profile")
)
expectEqual(
	"the personal-profile cold launch runs in the login-shell environment so the nix-profile launcher resolves on PATH",
	true,
	captures.lastExecuteRanInUserEnvironment
)

local nonStandardPersonalWindow = withTitle(makeFakeWindow(7, false), "Picture in picture - Google Chrome - Lucas")
setRunningApplications({
	["com.google.Chrome"] = { makeFakeApplication({ nonStandardPersonalWindow }) },
})
captures.currentlyFocusedWindowId = nil
captures.executedShellCommands = {}
summonPersonalProfile()

expectEqual("a non-standard personal-profile window is ignored", nil, captures.currentlyFocusedWindowId)
expectEqual(
	"the personal profile is cold-launched when only a non-standard personal window exists",
	1,
	timesShellCommandExecuted(captures.executedShellCommands, "summon-chrome-personal-profile")
)

setRunningApplications({})
captures.executedShellCommands = {}
summonPersonalProfile()

expectEqual(
	"the personal profile is cold-launched when Chrome is not running",
	1,
	timesShellCommandExecuted(captures.executedShellCommands, "summon-chrome-personal-profile")
)

harness.exitWithAccumulatedResult()
