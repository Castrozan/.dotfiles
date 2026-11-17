local stuckMouseButtonAdvisor = {}

local pollIntervalSeconds = 5
local stuckThresholdSeconds = 60
local nanosecondsPerSecond = 1000000000

function stuckMouseButtonAdvisor.heldButtonNames(pressedButtons)
	local names = {}
	for buttonName, isPressed in pairs(pressedButtons) do
		if type(buttonName) == "string" and isPressed then
			names[#names + 1] = buttonName
		end
	end
	table.sort(names)
	return table.concat(names, "+")
end

function stuckMouseButtonAdvisor.newHoldTracker(thresholdSeconds)
	local heldButtons = ""
	local heldSinceSeconds = nil
	local advisedForCurrentHold = false
	return function(currentlyHeldButtons, nowSeconds)
		if currentlyHeldButtons == "" then
			heldButtons, heldSinceSeconds, advisedForCurrentHold = "", nil, false
			return nil
		end
		if currentlyHeldButtons ~= heldButtons then
			heldButtons, heldSinceSeconds, advisedForCurrentHold = currentlyHeldButtons, nowSeconds, false
			return nil
		end
		if advisedForCurrentHold or nowSeconds - heldSinceSeconds < thresholdSeconds then
			return nil
		end
		advisedForCurrentHold = true
		return heldButtons
	end
end

local function adviseReplug(stuckButtons)
	hs.notify
		.new({
			title = "Mouse button stuck",
			informativeText = string.format(
				"macOS has read the %s mouse button as held for over a minute, so pointer moves act as drags"
					.. " and the menu bar will not reveal. Replug the monitor to reset the mouse receiver.",
				stuckButtons
			),
			withdrawAfter = 0,
		})
		:send()
end

function stuckMouseButtonAdvisor.start()
	local observeHold = stuckMouseButtonAdvisor.newHoldTracker(stuckThresholdSeconds)
	stuckMouseButtonAdvisor.heldButtonPoll = hs.timer.doEvery(pollIntervalSeconds, function()
		local stuckButtons = observeHold(
			stuckMouseButtonAdvisor.heldButtonNames(hs.mouse.getButtons()),
			hs.timer.absoluteTime() / nanosecondsPerSecond
		)
		if stuckButtons then
			adviseReplug(stuckButtons)
		end
	end)
	return stuckMouseButtonAdvisor
end

return stuckMouseButtonAdvisor
