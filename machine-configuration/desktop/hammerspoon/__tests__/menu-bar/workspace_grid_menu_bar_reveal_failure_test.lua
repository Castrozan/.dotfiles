local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local environment = require("menu_bar_reveal_test_environment")
local expectEqual = environment.expectEqual
local describeCommand = environment.describeCommand

local function scheduledWorkCount()
	return #environment.pendingTimers() + #environment.runningCommands()
end

local menuBarReveal = environment.loadFreshMenuBarReveal()
menuBarReveal.brieflyReveal()
environment.settleFocus()
environment.exitRunningCommand(1, "", "execution error")
expectEqual("an unavailable API is reported without selecting a menu", 1, #environment.reportedFailures)
expectEqual(
	"a failed reveal is released instead of retried",
	"hide 2",
	describeCommand(environment.launchedCommands[2])
)
environment.exitRunningCommand()
expectEqual("an unavailable API does not schedule a hide", 0, #environment.pendingTimers())
expectEqual("a failed reveal starts nothing further", 2, #environment.launchedCommands)
menuBarReveal.brieflyReveal()
environment.settleFocus()
environment.exitRunningCommand(0, "1001\n", "")
expectEqual("a native failure is reported", 2, #environment.reportedFailures)
environment.exitRunningCommand()
expectEqual("a rejected visibility override does not schedule a hide", 0, #environment.pendingTimers())
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual("a failed reveal does not block later reveals", "show 2", describeCommand(environment.launchedCommands[5]))
environment.exitRunningCommand()
environment.finishVisibleDuration()
environment.exitRunningCommand(1, "", "execution error")
expectEqual("a release failure is reported", 3, #environment.reportedFailures)
expectEqual("a failed release is not retried", 0, scheduledWorkCount())
menuBarReveal.brieflyReveal()
environment.settleFocus()
environment.runningCommands()[1]:exit(1, nil, nil)
expectEqual("a command that exits without readable output is reported", 4, #environment.reportedFailures)
environment.exitRunningCommand()
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual("a command without readable output does not block later reveals", 1, #environment.runningCommands())

menuBarReveal = environment.loadFreshMenuBarReveal()
environment.commandStarts = function()
	return false
end
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual("a script runner that cannot start is reported", 1, #environment.reportedFailures)
expectEqual("a script runner that cannot start leaves nothing scheduled", 0, scheduledWorkCount())
environment.commandStarts = function()
	return true
end
menuBarReveal.brieflyReveal()
environment.settleFocus()
expectEqual("a script runner that could not start does not block later reveals", 1, #environment.launchedCommands)

menuBarReveal = environment.loadFreshMenuBarReveal()
menuBarReveal.brieflyReveal()
menuBarReveal.releaseBeforeShutdown()
expectEqual("shutdown before focus settles stops the reveal", true, environment.timers[1].stopped)
expectEqual("shutdown before focus settles changes nothing", 0, #environment.launchedCommands)

menuBarReveal = environment.loadFreshMenuBarReveal()
menuBarReveal.brieflyReveal()
environment.settleFocus()
menuBarReveal.releaseBeforeShutdown()
expectEqual("shutdown waits for the running command", true, environment.launchedCommands[1].waitedSynchronously)
expectEqual("shutdown releases the revealed display", "hide 2", describeCommand(environment.launchedCommands[2]))
expectEqual("shutdown waits for the release to apply", true, environment.launchedCommands[2].waitedSynchronously)
expectEqual("shutdown leaves no display forced visible", 0, environment.forcedVisibleDisplayCount())

menuBarReveal = environment.loadFreshMenuBarReveal()
menuBarReveal.brieflyReveal()
environment.settleFocus()
environment.exitRunningCommand()
menuBarReveal.releaseBeforeShutdown()
expectEqual("shutdown stops the visible duration", 0, #environment.pendingTimers())
expectEqual("shutdown during the visible duration releases the display", 0, environment.forcedVisibleDisplayCount())

environment.exitWithAccumulatedResult()
