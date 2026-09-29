local dockStartupGuard = {}
local dockLaunchWatcher

local function stopDockLaunchWatcher()
	if dockLaunchWatcher then
		dockLaunchWatcher:stop()
		dockLaunchWatcher = nil
	end
end

function dockStartupGuard.allowStartup()
	stopDockLaunchWatcher()
	dockLaunchWatcher = hs.application.watcher.new(function(_, eventType, application)
		if not dockLaunchWatcher or eventType ~= hs.application.watcher.launched or not application then
			return
		end
		if application:bundleID() ~= "com.apple.dock" then
			return
		end
		if not hs.application.applicationsForBundleID("com.apple.dock")[1] then
			return
		end
		stopDockLaunchWatcher()
		hs.reload()
	end)
	dockLaunchWatcher:start()
	if not hs.application.applicationsForBundleID("com.apple.dock")[1] then
		return false
	end
	stopDockLaunchWatcher()
	return true
end

return dockStartupGuard
