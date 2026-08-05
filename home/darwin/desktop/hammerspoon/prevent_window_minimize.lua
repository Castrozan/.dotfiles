local preventWindowMinimize = {}

local onScreenWindows = require("window_server_on_screen_windows")

local periodicUnminimizeSweepIntervalInSeconds = 2

local ownerNameByWindowIdAtPreviousSweep = {}

local function unminimizeWindowIfMinimized(window)
	if window and window:isMinimized() then
		window:unminimize()
	end
end

local function unminimizeEveryMinimizedWindow()
	for _, window in ipairs(hs.window.allWindows()) do
		unminimizeWindowIfMinimized(window)
	end
end

local function anyWindowLeftTheScreenSincePreviousSweep(ownerNameByWindowIdNow)
	for previousWindowId in pairs(ownerNameByWindowIdAtPreviousSweep) do
		if ownerNameByWindowIdNow[previousWindowId] == nil then
			return true
		end
	end
	return false
end

local function sweepOnlyWhenAWindowLeftTheScreen()
	local ownerNameByWindowIdNow = onScreenWindows.ownerNameByWindowId()
	local aWindowLeftTheScreen = anyWindowLeftTheScreenSincePreviousSweep(ownerNameByWindowIdNow)
	ownerNameByWindowIdAtPreviousSweep = ownerNameByWindowIdNow
	if aWindowLeftTheScreen then
		unminimizeEveryMinimizedWindow()
	end
end

preventWindowMinimize.sweepOnlyWhenAWindowLeftTheScreen = sweepOnlyWhenAWindowLeftTheScreen

function preventWindowMinimize.start()
	preventWindowMinimize.windowMinimizeWatcher = hs.window.filter.new()
	preventWindowMinimize.windowMinimizeWatcher:subscribe(hs.window.filter.windowMinimized, function(window)
		unminimizeWindowIfMinimized(window)
	end)
	preventWindowMinimize.periodicUnminimizeSweep =
		hs.timer.doEvery(periodicUnminimizeSweepIntervalInSeconds, sweepOnlyWhenAWindowLeftTheScreen)
	unminimizeEveryMinimizedWindow()
	ownerNameByWindowIdAtPreviousSweep = onScreenWindows.ownerNameByWindowId()
	return preventWindowMinimize
end

return preventWindowMinimize
