local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local accessibilityEnumerationCallCount = 0
local unminimizeCallCountByWindowId = {}
local minimizedWindowIds = {}
local onScreenWindowIds = { 801, 802, 803 }
local scheduledSweep = nil

local function makeFakeWindow(windowId)
	local fakeWindow = {}
	function fakeWindow:id()
		return windowId
	end
	function fakeWindow:isMinimized()
		return minimizedWindowIds[windowId] == true
	end
	function fakeWindow:unminimize()
		minimizedWindowIds[windowId] = nil
		unminimizeCallCountByWindowId[windowId] = (unminimizeCallCountByWindowId[windowId] or 0) + 1
	end
	return fakeWindow
end

local everyWindow = { makeFakeWindow(801), makeFakeWindow(802), makeFakeWindow(803) }

hs = {
	timer = {
		doEvery = function(_, sweepFunction)
			scheduledSweep = sweepFunction
			return { start = function() end, stop = function() end }
		end,
	},
	window = {
		allWindows = function()
			accessibilityEnumerationCallCount = accessibilityEnumerationCallCount + 1
			return everyWindow
		end,
		list = function()
			local windowServerEntries = {}
			for _, windowId in ipairs(onScreenWindowIds) do
				windowServerEntries[#windowServerEntries + 1] =
					{ kCGWindowNumber = windowId, kCGWindowOwnerName = "FakeApp" }
			end
			return windowServerEntries
		end,
		filter = {
			windowMinimized = "windowMinimized",
			new = function()
				return { subscribe = function() end }
			end,
		},
	},
}

local preventWindowMinimize = require("prevent_window_minimize")

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

preventWindowMinimize.start()
expectEqual("startup sweeps once so an already minimized window is caught", 1, accessibilityEnumerationCallCount)

for _ = 1, 30 do
	scheduledSweep()
end
expectEqual(
	"a sweep tick where no window left the screen queries no application over accessibility"
		.. " (hs.window.allWindows costs 38ms on rin and this timer runs every 2 seconds forever)",
	1,
	accessibilityEnumerationCallCount
)

minimizedWindowIds[802] = true
onScreenWindowIds = { 801, 803 }
scheduledSweep()
expectEqual("a window leaving the screen still triggers the accessibility sweep", 2, accessibilityEnumerationCallCount)
expectEqual("the window that minimized was unminimized by that sweep", 1, unminimizeCallCountByWindowId[802])
expectEqual("no other window was touched", nil, unminimizeCallCountByWindowId[801])

onScreenWindowIds = { 801, 802, 803 }
scheduledSweep()
expectEqual(
	"the window coming back on screen is an addition, not a loss, so it triggers no sweep",
	2,
	accessibilityEnumerationCallCount
)

os.exit(failureCount == 0 and 0 or 1)
