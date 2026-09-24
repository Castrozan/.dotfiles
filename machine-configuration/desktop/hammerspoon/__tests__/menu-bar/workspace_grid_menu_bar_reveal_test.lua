local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local timers = {}
local visibilityChanges = {}
local focusedDisplayId = 2
local mainDisplayId = 1
local scriptSucceeds = true
local nativeResult = 0
local reportedFailures = {}

local function makeTimer(delaySeconds, callback)
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
end

local function makeScreen(displayId)
	if displayId then
		return {
			id = function()
				return displayId
			end,
		}
	end
end

hs = {
	window = {
		focusedWindow = function()
			if focusedDisplayId then
				return {
					screen = function()
						return makeScreen(focusedDisplayId)
					end,
				}
			end
		end,
	},
	screen = {
		mainScreen = function()
			return makeScreen(mainDisplayId)
		end,
	},
	application = {
		frontmostApplication = function()
			error("revealing the bar must not select an application menu")
		end,
	},
	timer = { doAfter = makeTimer },
	osascript = {
		javascript = function(source)
			local displayId, visible = source:match(
				"%$%.SLSSetMenuBarVisibilityOverrideOnDisplay%(%$%.SLSMainConnectionID%(%), (%d+), (%a+)%)"
			)
			assert(displayId and visible, "visibility must use the native display override")
			table.insert(visibilityChanges, { displayId = tonumber(displayId), visible = visible == "true" })
			return scriptSucceeds, nativeResult
		end,
	},
	printf = function(...)
		table.insert(reportedFailures, string.format(...))
	end,
}

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print("PASS: " .. description)
	end
end

local menuBarReveal = require("workspace_grid_menu_bar_reveal")
menuBarReveal.brieflyReveal()
expectEqual("reveal waits for workspace focus to settle", 0, timers[1].delaySeconds)
expectEqual("the old workspace is not revealed", 0, #visibilityChanges)
timers[1]:fire()
expectEqual("the focused window determines the display", 2, visibilityChanges[1].displayId)
expectEqual("reveal changes visibility without selecting a menu", true, visibilityChanges[1].visible)
expectEqual("the menu bar remains visible for one second", 1, timers[2].delaySeconds)
timers[2]:fire()
expectEqual("the timer releases the native visibility override", false, visibilityChanges[2].visible)

menuBarReveal.brieflyReveal()
timers[3]:fire()
focusedDisplayId = 3
menuBarReveal.brieflyReveal()
expectEqual("another reveal cancels the old hide timer", true, timers[4].stopped)
expectEqual("another reveal releases the old display", 2, visibilityChanges[4].displayId)
expectEqual("the old display is no longer forced visible", false, visibilityChanges[4].visible)
timers[5]:fire()
expectEqual("the replacement reveal uses the new display", 3, visibilityChanges[5].displayId)
timers[4]:fire()
expectEqual("the stale timer cannot hide the new reveal", 5, #visibilityChanges)
menuBarReveal.cancel()
expectEqual("cancelling stops the active hide timer", true, timers[6].stopped)
expectEqual("cancelling releases the active display", 3, visibilityChanges[6].displayId)
expectEqual("cancelling removes the visibility override", false, visibilityChanges[6].visible)

menuBarReveal.brieflyReveal()
menuBarReveal.cancel()
timers[7]:fire()
expectEqual("cancellation before focus settles changes nothing", 6, #visibilityChanges)

focusedDisplayId = nil
menuBarReveal.brieflyReveal()
timers[8]:fire()
expectEqual("an empty workspace uses the main display", 1, visibilityChanges[7].displayId)
timers[9]:fire()

mainDisplayId = nil
menuBarReveal.brieflyReveal()
timers[10]:fire()
expectEqual("a missing display does not change visibility", 8, #visibilityChanges)
mainDisplayId = 1

scriptSucceeds = false
menuBarReveal.brieflyReveal()
timers[11]:fire()
expectEqual("an unavailable API does not schedule a hide", 11, #timers)
expectEqual("an unavailable API is reported without selecting a menu", 1, #reportedFailures)
scriptSucceeds = true
nativeResult = 1001
menuBarReveal.brieflyReveal()
timers[12]:fire()
expectEqual("a rejected visibility override does not schedule a hide", 12, #timers)
expectEqual("a native failure is reported", 2, #reportedFailures)
nativeResult = 0
menuBarReveal.brieflyReveal()
timers[13]:fire()
expectEqual("a failed reveal does not block later reveals", 14, #timers)
nativeResult = 1002
timers[14]:fire()
expectEqual("a release failure is reported", 3, #reportedFailures)

os.exit(failureCount == 0 and 0 or 1)
