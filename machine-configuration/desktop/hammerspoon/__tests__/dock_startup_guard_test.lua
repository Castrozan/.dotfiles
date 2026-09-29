local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local originalRequire = require
local dockApplications = {}
local startupTimer
local reloadCount = 0
local focusWatcherStartCount = 0
local windowSetupCount = 0
local warningCount = 0
local dockLookupCount = 0
local windowSetupReached = {}

hs = {
	application = {
		applicationsForBundleID = function(bundleIdentifier)
			assert(bundleIdentifier == "com.apple.dock")
			dockLookupCount = dockLookupCount + 1
			return dockApplications
		end,
	},
	timer = {
		doEvery = function(interval, callback)
			assert(interval == 0.5, "Dock readiness must be sampled at most twice a second")
			startupTimer = {
				callback = callback,
				running = true,
				stop = function(self)
					self.running = false
				end,
			}
			return startupTimer
		end,
	},
	logger = {
		new = function()
			return {
				e = function(_, message)
					assert(message:find("60 seconds", 1, true))
					warningCount = warningCount + 1
				end,
			}
		end,
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
assert(startupTimer and startupTimer.running, "Dock recovery must not depend on application launch notifications")
startupTimer.callback()
assert(reloadCount == 0, "an unavailable Dock must not reload")

dockApplications = { {} }
startupTimer.callback()
assert(reloadCount == 1, "Dock becoming available without a launch event must reload")
assert(not startupTimer.running, "the retry timer must stop before reloading")
startupTimer.callback()
assert(reloadCount == 1, "queued callbacks must not reload twice")

local readyStartupSucceeded, startupResult = pcall(dofile, moduleDirectory .. "init.lua")
assert(not readyStartupSucceeded and startupResult == windowSetupReached, "a running Dock must allow normal startup")
assert(windowSetupCount == 1, "window setup must run once when Dock is available")
assert(focusWatcherStartCount == 2, "Karabiner focus updates must also start with Dock available")
assert(not startupTimer.running, "normal startup must retain no running timer")

dockApplications = {}
local guard = require("dock_startup_guard")
assert(not guard.allowStartup())
local lookupCountBeforeRetries = dockLookupCount
for _ = 1, 120 do
	assert(startupTimer.running, "startup retries must allow up to 60 seconds for Dock")
	startupTimer.callback()
end
assert(not startupTimer.running, "startup retries must stop after 60 seconds")
assert(dockLookupCount - lookupCountBeforeRetries == 120, "one retry must perform exactly one Dock lookup")
assert(warningCount == 1, "an exhausted startup wait must report the recovery action once")
startupTimer.callback()
assert(warningCount == 1 and reloadCount == 1, "a stopped retry must do no further work")

dockApplications = { {} }
assert(guard.allowStartup(), "startup may be retried after Dock returns")
assert(not startupTimer.running, "successful startup must not restart polling")

require = originalRequire
print("PASS: bounded startup retries recover without Dock launch events and preserve Karabiner focus updates")
