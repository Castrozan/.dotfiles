local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local originalRequire = require
local dockApplications = {}
local applicationWatcher
local reloadCount = 0
local focusWatcherStartCount = 0
local windowSetupCount = 0
local windowSetupReached = {}

hs = {
	application = {
		applicationsForBundleID = function(bundleIdentifier)
			assert(bundleIdentifier == "com.apple.dock")
			return dockApplications
		end,
		watcher = {
			launched = 1,
			terminated = 2,
			new = function(callback)
				applicationWatcher = {
					callback = callback,
					start = function(self)
						self.running = true
						return self
					end,
					stop = function(self)
						self.running = false
					end,
				}
				return applicationWatcher
			end,
		},
	},
	reload = function()
		reloadCount = reloadCount + 1
	end,
}

require = function(moduleName)
	if moduleName == "hs.ipc" then
		return true
	end
	if moduleName == "karabiner_application_focus_variables" then
		return {
			start = function()
				focusWatcherStartCount = focusWatcherStartCount + 1
			end,
		}
	end
	if moduleName == "workspace_grid" then
		windowSetupCount = windowSetupCount + 1
		error(windowSetupReached)
	end
	return originalRequire(moduleName)
end

local startupSucceeded = pcall(dofile, moduleDirectory .. "init.lua")
assert(startupSucceeded, "startup must defer window setup when Dock is absent")
assert(focusWatcherStartCount == 1, "Karabiner focus updates must start while Dock is absent")
assert(windowSetupCount == 0, "no window setup may run before Dock is available")
assert(applicationWatcher.running, "Dock launch must be observed without polling")

local dockApplication = {
	bundleID = function()
		return "com.apple.dock"
	end,
}
local otherApplication = {
	bundleID = function()
		return "com.apple.finder"
	end,
}
applicationWatcher.callback("Finder", hs.application.watcher.launched, otherApplication)
applicationWatcher.callback(nil, hs.application.watcher.terminated, dockApplication)
applicationWatcher.callback("Dock", hs.application.watcher.launched, nil)
applicationWatcher.callback("Dock", hs.application.watcher.launched, dockApplication)
assert(reloadCount == 0, "unrelated events and an unavailable Dock must not reload")

dockApplications = { dockApplication }
applicationWatcher.callback("Dock", hs.application.watcher.launched, dockApplication)
assert(reloadCount == 1, "Dock becoming available must reload the configuration")
assert(not applicationWatcher.running, "the startup watcher must stop before reloading")
applicationWatcher.callback("Dock", hs.application.watcher.launched, dockApplication)
assert(reloadCount == 1, "queued events must not reload twice")

package.loaded.dock_startup_guard = nil
local readyStartupSucceeded, startupResult = pcall(dofile, moduleDirectory .. "init.lua")
assert(not readyStartupSucceeded and startupResult == windowSetupReached, "a running Dock must allow normal startup")
assert(windowSetupCount == 1, "window setup must run once when Dock is available")
assert(focusWatcherStartCount == 2, "Karabiner focus updates must also start with Dock available")
assert(not applicationWatcher.running, "normal startup must retain no application watcher")

require = originalRequire
print("PASS: startup defers for Dock, resumes once, and preserves Karabiner focus updates")
