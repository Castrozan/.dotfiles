local applicationWatcherElementCache = {}
local installed = false

function applicationWatcherElementCache.install()
	if installed then
		return
	end

	local applicationMetatable = hs.getObjectMetatable("hs.application")
	local watcherMetatable = hs.getObjectMetatable("hs.uielement.watcher")
	local originalNewWatcher = applicationMetatable.newWatcher
	local originalElement = watcherMetatable.element
	local applicationsByWatcher = setmetatable({}, { __mode = "k" })

	applicationMetatable.newWatcher = function(application, ...)
		local watcher = originalNewWatcher(application, ...)
		if watcher then
			applicationsByWatcher[watcher] = application
		end
		return watcher
	end

	watcherMetatable.element = function(watcher)
		return applicationsByWatcher[watcher] or originalElement(watcher)
	end

	installed = true
end

return applicationWatcherElementCache
