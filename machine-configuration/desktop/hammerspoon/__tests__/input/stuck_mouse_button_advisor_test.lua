local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local scheduledPoll = nil
local scheduledPollIntervalSeconds = nil
local currentPressedButtons = {}
local currentNanoseconds = 0
local sentNotifications = {}

hs = {
	timer = {
		doEvery = function(intervalSeconds, pollFunction)
			scheduledPollIntervalSeconds = intervalSeconds
			scheduledPoll = pollFunction
			return { stop = function() end }
		end,
		absoluteTime = function()
			return currentNanoseconds
		end,
	},
	mouse = {
		getButtons = function()
			return currentPressedButtons
		end,
	},
	notify = {
		new = function(attributes)
			return {
				send = function()
					sentNotifications[#sentNotifications + 1] = attributes
				end,
			}
		end,
	},
}

local advisor = require("stuck_mouse_button_advisor")

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

local thresholdSeconds = 60
local heldButtonChoices = { "", "left", "right", "left+right" }

local function randomSamples()
	local samples = {}
	local nowSeconds = math.random(0, 1000)
	for _ = 1, math.random(1, 8) do
		local heldButtons = heldButtonChoices[math.random(#heldButtonChoices)]
		for _ = 1, math.random(1, 25) do
			nowSeconds = nowSeconds + math.random(1, 20)
			samples[#samples + 1] = { heldButtons = heldButtons, nowSeconds = nowSeconds }
		end
	end
	return samples
end

local function brokenRuleIn(samples)
	local observeHold = advisor.newHoldTracker(thresholdSeconds)
	local runStartIndex = 1
	local adviceCountInRun = 0
	for sampleIndex, sample in ipairs(samples) do
		if sampleIndex > 1 and sample.heldButtons ~= samples[sampleIndex - 1].heldButtons then
			runStartIndex = sampleIndex
			adviceCountInRun = 0
		end
		local advice = observeHold(sample.heldButtons, sample.nowSeconds)
		local heldLongEnough = sample.nowSeconds - samples[runStartIndex].nowSeconds >= thresholdSeconds
		if advice then
			adviceCountInRun = adviceCountInRun + 1
			if sample.heldButtons == "" then
				return "advised while no button was held"
			end
			if advice ~= sample.heldButtons then
				return "advised a button other than the one held"
			end
			if not heldLongEnough then
				return "advised before the hold reached the threshold"
			end
			if adviceCountInRun > 1 then
				return "advised twice for one continuous hold"
			end
		elseif sample.heldButtons ~= "" and heldLongEnough and adviceCountInRun == 0 then
			return "stayed silent after the hold reached the threshold"
		end
	end
	return nil
end

math.randomseed(20261117)
local brokenSequenceDescriptions = {}
for sequenceNumber = 1, 500 do
	local brokenRule = brokenRuleIn(randomSamples())
	if brokenRule then
		brokenSequenceDescriptions[#brokenSequenceDescriptions + 1] =
			string.format("sequence %d: %s", sequenceNumber, brokenRule)
	end
end
expectEqual(
	"random hold sequences advise exactly once per continuous hold that reaches the threshold, never otherwise",
	"",
	table.concat(brokenSequenceDescriptions, "; ")
)

expectEqual(
	"held button names ignore the positional entries hs.mouse.getButtons also returns",
	"right",
	advisor.heldButtonNames({ false, true, right = true })
)
expectEqual("no pressed button reads as no hold", "", advisor.heldButtonNames({}))

local function pollAfterSeconds(elapsedSeconds)
	currentNanoseconds = currentNanoseconds + elapsedSeconds * 1000000000
	scheduledPoll()
end

advisor.start()
expectEqual("the poll runs every five seconds", 5, scheduledPollIntervalSeconds)

currentPressedButtons = { false, true, right = true }
pollAfterSeconds(0)
for _ = 1, 11 do
	pollAfterSeconds(5)
end
expectEqual("a right button held for 55 seconds sends no advice", 0, #sentNotifications)

pollAfterSeconds(5)
expectEqual("a right button held for 60 seconds sends one advice", 1, #sentNotifications)
expectEqual(
	"the advice names the held button and tells you to replug the monitor",
	true,
	sentNotifications[1].informativeText:find("right mouse button", 1, true) ~= nil
		and sentNotifications[1].informativeText:find("Replug the monitor", 1, true) ~= nil
)

for _ = 1, 20 do
	pollAfterSeconds(5)
end
expectEqual("the same stuck hold never repeats its advice", 1, #sentNotifications)

currentPressedButtons = {}
pollAfterSeconds(5)
currentPressedButtons = { false, true, right = true }
pollAfterSeconds(5)
for _ = 1, 12 do
	pollAfterSeconds(5)
end
expectEqual("a new stuck hold after a release advises again", 2, #sentNotifications)

os.exit(failureCount == 0 and 0 or 1)
