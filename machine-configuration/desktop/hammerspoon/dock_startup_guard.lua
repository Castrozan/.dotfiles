local dockStartupGuard = {}
local startupRetryTimer
local retryIntervalSeconds = 0.5
local maximumRetryCount = 120

local function stopStartupRetryTimer()
	if startupRetryTimer then
		startupRetryTimer:stop()
		startupRetryTimer = nil
	end
end

function dockStartupGuard.allowStartup()
	stopStartupRetryTimer()
	if hs.application.applicationsForBundleID("com.apple.dock")[1] then
		return true
	end
	local remainingRetries = maximumRetryCount
	startupRetryTimer = hs.timer.doEvery(retryIntervalSeconds, function()
		if not startupRetryTimer then
			return
		end
		if hs.application.applicationsForBundleID("com.apple.dock")[1] then
			stopStartupRetryTimer()
			hs.reload()
			return
		end
		remainingRetries = remainingRetries - 1
		if remainingRetries == 0 then
			stopStartupRetryTimer()
			hs.logger.new("dock-startup"):e("Dock unavailable for 60 seconds; reload Hammerspoon after Dock starts")
		end
	end)
	return false
end

return dockStartupGuard
