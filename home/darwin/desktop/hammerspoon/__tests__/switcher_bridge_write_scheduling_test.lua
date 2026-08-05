local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local windowsFileWriteCount = 0
local realFileOpen = io.open
io.open = function(filePath, mode)
	if filePath == "/tmp/workspace-window-switcher-windows.json" then
		windowsFileWriteCount = windowsFileWriteCount + 1
		return {
			write = function() end,
			close = function() end,
		}
	end
	return realFileOpen(filePath, mode)
end

local repeatingTimerCount = 0
local pendingDelayedCallback = nil

hs.json = {
	encode = function()
		return "{}"
	end,
}
hs.timer = {
	doEvery = function()
		repeatingTimerCount = repeatingTimerCount + 1
		return { start = function() end, stop = function() end }
	end,
	doAfter = function(_, callback)
		pendingDelayedCallback = callback
		return {
			stop = function()
				pendingDelayedCallback = nil
			end,
		}
	end,
}
hs.pathwatcher = {
	new = function()
		return { start = function() end }
	end,
}

local subscribedEventNames = {}
hs.window.filter.windowCreated = "windowCreated"
hs.window.filter.windowDestroyed = "windowDestroyed"
hs.window.filter.windowFocused = "windowFocused"
hs.window.filter.windowTitleChanged = "windowTitleChanged"
hs.window.filter.new = function()
	return {
		subscribe = function(_, eventNames, callback)
			for _, eventName in ipairs(eventNames) do
				subscribedEventNames[eventName] = callback
			end
		end,
	}
end

local function fireAnyPendingDelayedCallback()
	local callbackToFire = pendingDelayedCallback
	pendingDelayedCallback = nil
	if callbackToFire then
		callbackToFire()
	end
end

harness.setLiveWindowsToIds({ 501, 502 })
local grid = harness.loadFreshGrid()
package.loaded["switcher_bridge"] = nil
local switcherBridge = require("switcher_bridge")

expectEqual("the bridge writes the file once at startup so the daemon is never cold", 1, windowsFileWriteCount)
expectEqual(
	"no repeating timer is armed, because a 1Hz rewrite cost 0.80% of a core whether or not anything changed",
	0,
	repeatingTimerCount
)

for _, eventName in ipairs({ "windowCreated", "windowDestroyed", "windowFocused", "windowTitleChanged" }) do
	expectEqual("the bridge subscribes to " .. eventName, "function", type(subscribedEventNames[eventName]))
end

windowsFileWriteCount = 0
fireAnyPendingDelayedCallback()
expectEqual("an idle bridge writes nothing at all", 0, windowsFileWriteCount)

subscribedEventNames["windowCreated"]()
subscribedEventNames["windowFocused"]()
subscribedEventNames["windowTitleChanged"]()
expectEqual("a burst of window events writes nothing before the coalescing delay elapses", 0, windowsFileWriteCount)
fireAnyPendingDelayedCallback()
expectEqual("a burst of window events collapses into a single write", 1, windowsFileWriteCount)

windowsFileWriteCount = 0
grid.switchToWorkspace(4)
fireAnyPendingDelayedCallback()
expectEqual(
	"switching to a workspace refreshes the file, because no window event fires when the workspace is empty",
	1,
	windowsFileWriteCount
)

windowsFileWriteCount = 0
switcherBridge.writeCurrentWorkspaceWindowsFile()
expectEqual("the daemon can still be served a file written on demand", 1, windowsFileWriteCount)

io.open = realFileOpen

harness.exitWithAccumulatedStatus()
