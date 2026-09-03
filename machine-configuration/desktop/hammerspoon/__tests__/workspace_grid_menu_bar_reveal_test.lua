local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local mousePosition = { x = 640, y = 480 }
local currentScreen = {
	fullFrame = function()
		return { x = 0, y = -900, w = 1440, h = 900 }
	end,
}
local postedMouseEvents = {}
local timers = {}

local function copyPoint(point)
	return { x = point.x, y = point.y }
end

hs = {
	eventtap = {
		event = {
			types = { mouseMoved = "mouseMoved" },
			newMouseEvent = function(eventType, point)
				return {
					post = function()
						mousePosition = copyPoint(point)
						table.insert(postedMouseEvents, { eventType = eventType, point = copyPoint(point) })
					end,
				}
			end,
		},
	},
	mouse = {
		absolutePosition = function(point)
			if point then
				mousePosition = copyPoint(point)
			end
			return copyPoint(mousePosition)
		end,
		getCurrentScreen = function()
			return currentScreen
		end,
	},
	timer = {
		doAfter = function(delaySeconds, callback)
			local timer = { delaySeconds = delaySeconds, stopped = false }
			function timer:stop()
				self.stopped = true
			end
			function timer:fire()
				if not self.stopped then
					self.stopped = true
					callback()
				end
			end
			table.insert(timers, timer)
			return timer
		end,
	},
}

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

local menuBarReveal = require("workspace_grid_menu_bar_reveal")

menuBarReveal.brieflyReveal()
expectEqual("revealing uses one native mouse-move event", 1, #postedMouseEvents)
expectEqual("the reveal keeps the cursor's horizontal position", 640, postedMouseEvents[1].point.x)
expectEqual("the reveal reaches the current screen's top edge", -900, postedMouseEvents[1].point.y)
expectEqual("the cursor return delay is short enough to be unobtrusive", 0.12, timers[1].delaySeconds)
expectEqual("the menu bar remains visible briefly", 1, timers[2].delaySeconds)

timers[1]:fire()
expectEqual("the cursor returns to its original horizontal position", 640, mousePosition.x)
expectEqual("the cursor returns to its original vertical position", 480, mousePosition.y)

timers[2]:fire()
expectEqual("the hide emits one mouse-move event after the reveal", 2, #postedMouseEvents)
expectEqual("the hide event does not move the cursor horizontally", 640, postedMouseEvents[2].point.x)
expectEqual("the hide event does not move the cursor vertically", 480, postedMouseEvents[2].point.y)

mousePosition = { x = 400, y = 500 }
menuBarReveal.brieflyReveal()
menuBarReveal.brieflyReveal()
expectEqual("a repeated reveal cancels the previous cursor timer", true, timers[3].stopped)
expectEqual("a repeated reveal cancels the previous hide timer", true, timers[4].stopped)
timers[5]:fire()
expectEqual("a repeated reveal preserves the original cursor position", 400, mousePosition.x)
expectEqual("a repeated reveal preserves the original cursor row", 500, mousePosition.y)
timers[6]:fire()

mousePosition = { x = 300, y = 600 }
menuBarReveal.brieflyReveal()
hs.mouse.absolutePosition({ x = 350, y = 650 })
timers[7]:fire()
expectEqual("user cursor movement is not overwritten horizontally", 350, mousePosition.x)
expectEqual("user cursor movement is not overwritten vertically", 650, mousePosition.y)
timers[8]:fire()

mousePosition = { x = 200, y = 700 }
menuBarReveal.brieflyReveal()
menuBarReveal.cancel()
expectEqual("cancelling restores a cursor still parked at the top edge", 200, mousePosition.x)
expectEqual("cancelling restores the cursor's original row", 700, mousePosition.y)
expectEqual("cancelling stops the pending cursor timer", true, timers[9].stopped)
expectEqual("cancelling stops the pending hide timer", true, timers[10].stopped)

os.exit(failureCount == 0 and 0 or 1)
