local preventWindowMinimize = {}

local periodicUnminimizeSweepIntervalInSeconds = 2

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

function preventWindowMinimize.start()
	preventWindowMinimize.windowMinimizeWatcher = hs.window.filter.new()
	preventWindowMinimize.windowMinimizeWatcher:subscribe(hs.window.filter.windowMinimized, function(window)
		unminimizeWindowIfMinimized(window)
	end)
	preventWindowMinimize.periodicUnminimizeSweep =
		hs.timer.doEvery(periodicUnminimizeSweepIntervalInSeconds, unminimizeEveryMinimizedWindow)
	unminimizeEveryMinimizedWindow()
	return preventWindowMinimize
end

return preventWindowMinimize
