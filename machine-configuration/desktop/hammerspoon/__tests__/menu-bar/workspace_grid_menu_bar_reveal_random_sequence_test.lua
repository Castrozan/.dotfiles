local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local environment = require("menu_bar_reveal_test_environment")

local randomSequenceCount = 400
local eventsPerSequence = 40
local settlingRoundCount = 20
local revealableDisplayIds = { false, 1, 2, 3 }

local function runRandomSequence(sequenceNumber)
	local menuBarReveal = environment.loadFreshMenuBarReveal()
	environment.commandStarts = function(command)
		return not command.visible or math.random(8) > 1
	end
	local settledRevealCount = 0
	local function fireTimer(timer)
		if timer.delaySeconds == 0 then
			settledRevealCount = settledRevealCount + 1
		end
		timer:fire()
	end

	for _ = 1, eventsPerSequence do
		local eventKind = math.random(4)
		local pending, running = environment.pendingTimers(), environment.runningCommands()
		if eventKind == 1 then
			environment.focusedDisplayId = revealableDisplayIds[math.random(#revealableDisplayIds)] or nil
			menuBarReveal.brieflyReveal()
		elseif eventKind == 2 and #pending > 0 then
			fireTimer(pending[math.random(#pending)])
		elseif #running > 0 and running[1].visible and math.random(4) == 1 then
			running[1]:exit(1, "", "execution error")
		elseif #running > 0 then
			running[1]:exit(0, "0\n", "")
		end
	end

	local endsWithShutdown = sequenceNumber % 2 == 0
	if endsWithShutdown then
		menuBarReveal.releaseBeforeShutdown()
	else
		for _ = 1, settlingRoundCount do
			for _, command in ipairs(environment.runningCommands()) do
				command:exit(0, "0\n", "")
			end
			for _, timer in ipairs(environment.pendingTimers()) do
				fireTimer(timer)
			end
		end
	end

	if environment.highestConcurrentCommandCount > 1 then
		return "commands overlapped"
	end
	if environment.forcedVisibleDisplayCount() > 0 then
		return "a display stayed forced visible"
	end
	if endsWithShutdown then
		return nil
	end
	if #environment.pendingTimers() + #environment.runningCommands() > 0 then
		return "work never settled"
	end
	if #environment.launchedCommands > 2 * settledRevealCount then
		return "more than two processes per settled reveal"
	end
	return nil
end

math.randomseed(20261110)
local brokenSequenceDescriptions = {}
for sequenceNumber = 1, randomSequenceCount do
	local brokenRule = runRandomSequence(sequenceNumber)
	if brokenRule then
		table.insert(brokenSequenceDescriptions, string.format("sequence %d: %s", sequenceNumber, brokenRule))
	end
end
environment.expectEqual(
	"random reveal, timer, failure and shutdown sequences keep one command running and end hidden",
	"",
	table.concat(brokenSequenceDescriptions, "; ")
)

environment.exitWithAccumulatedResult()
