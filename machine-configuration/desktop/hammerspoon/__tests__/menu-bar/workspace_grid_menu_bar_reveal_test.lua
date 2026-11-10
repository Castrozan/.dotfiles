local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local environment = require("menu_bar_reveal_test_environment")
local expectEqual = environment.expectEqual
local describeCommand = environment.describeCommand

local menuBarReveal = environment.loadFreshMenuBarReveal()
local expectedCommandByRevealAndPossiblyVisibleDisplay = {
	["nil,nil"] = "none",
	["nil,1"] = "hide 1",
	["nil,2"] = "hide 2",
	["1,nil"] = "show 1",
	["1,1"] = "none",
	["1,2"] = "hide 2",
	["2,nil"] = "show 2",
	["2,1"] = "hide 1",
	["2,2"] = "none",
}
local decidedCellCount = 0
for _, displayIdToReveal in ipairs({ false, 1, 2 }) do
	for _, displayIdPossiblyVisible in ipairs({ false, 1, 2 }) do
		local cell = tostring(displayIdToReveal or nil) .. "," .. tostring(displayIdPossiblyVisible or nil)
		decidedCellCount = decidedCellCount + 1
		expectEqual(
			"reveal " .. cell .. " possibly visible decides the next command",
			expectedCommandByRevealAndPossiblyVisibleDisplay[cell],
			describeCommand(
				menuBarReveal.nextVisibilityCommand(displayIdToReveal or nil, displayIdPossiblyVisible or nil)
			)
		)
	end
end
expectEqual("every reveal and possibly visible display pair is decided", 9, decidedCellCount)

menuBarReveal.brieflyReveal()
expectEqual("reveal waits for workspace focus to settle", 0, environment.timers[1].delaySeconds)
expectEqual("the old workspace is not revealed", 0, #environment.launchedCommands)
environment.settleFocus()
local revealCommand = environment.launchedCommands[1]
expectEqual("the override runs in the system script runner", "/usr/bin/osascript", revealCommand.launchPath)
expectEqual(
	"the script runner evaluates JavaScript",
	"-l JavaScript -e",
	table.concat(revealCommand.arguments, " ", 1, 3)
)
expectEqual(
	"visibility uses the native display override",
	true,
	revealCommand.arguments[4]:find("SLSSetMenuBarVisibilityOverrideOnDisplay", 1, true) ~= nil
)
expectEqual("the focused window determines the display", 2, revealCommand.displayId)
expectEqual("reveal changes visibility without selecting a menu", true, revealCommand.visible)
expectEqual("the visible duration starts once the reveal applied", 0, #environment.pendingTimers())
environment.exitRunningCommand()
expectEqual("the menu bar remains visible for one second", 1, environment.pendingTimers()[1].delaySeconds)
local firstVisibleDurationTimer = environment.pendingTimers()[1]

menuBarReveal.brieflyReveal()
expectEqual("another reveal cancels the old hide timer", true, firstVisibleDurationTimer.stopped)
environment.settleFocus()
expectEqual("revealing the visible display again runs no command", 1, #environment.launchedCommands)
expectEqual("revealing the visible display again restarts its duration", 1, #environment.pendingTimers())
firstVisibleDurationTimer:fire()
expectEqual("the stale timer cannot hide the renewed reveal", 1, #environment.launchedCommands)

environment.focusedDisplayId = 3
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual(
	"another display first releases the old display",
	"hide 2",
	describeCommand(environment.launchedCommands[2])
)
environment.exitRunningCommand()
expectEqual("the replacement reveal uses the new display", "show 3", describeCommand(environment.launchedCommands[3]))
environment.exitRunningCommand()
environment.finishVisibleDuration()
expectEqual(
	"the timer releases the native visibility override",
	"hide 3",
	describeCommand(environment.launchedCommands[4])
)
environment.exitRunningCommand()
expectEqual("no display stays forced visible", 0, environment.forcedVisibleDisplayCount())
expectEqual(
	"a released menu bar leaves nothing scheduled",
	0,
	#environment.pendingTimers() + #environment.runningCommands()
)
expectEqual("commands never overlap", 1, environment.highestConcurrentCommandCount)

menuBarReveal = environment.loadFreshMenuBarReveal()
for _ = 1, 50 do
	menuBarReveal.brieflyReveal()
	environment.settleFocus()
end
expectEqual("fifty reveals during one slow command start one process", 1, #environment.launchedCommands)
environment.exitRunningCommand()
for _ = 1, 50 do
	menuBarReveal.brieflyReveal()
	environment.settleFocus()
end
environment.finishVisibleDuration()
environment.exitRunningCommand()
expectEqual("a hundred reveals of one display cost one show and one hide", 2, #environment.launchedCommands)

menuBarReveal = environment.loadFreshMenuBarReveal()
environment.focusedDisplayId = nil
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual("an empty workspace uses the main display", "show 1", describeCommand(environment.launchedCommands[1]))

menuBarReveal = environment.loadFreshMenuBarReveal()
environment.focusedDisplayId, environment.mainDisplayId = nil, nil
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual("a missing display does not change visibility", 0, #environment.launchedCommands)

environment.exitWithAccumulatedResult()
