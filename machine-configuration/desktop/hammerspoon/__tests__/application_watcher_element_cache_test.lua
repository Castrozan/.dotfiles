local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local applicationMetatable = {}
applicationMetatable.__index = applicationMetatable
local watcherMetatable = {}
watcherMetatable.__index = watcherMetatable
local nativeElementLookupCount = 0
local nativeWatcherCreationCount = 0
local failWatcherCreation = false

function applicationMetatable:isApplication()
	return true
end

function applicationMetatable:newWatcher(callback, userData)
	nativeWatcherCreationCount = nativeWatcherCreationCount + 1
	if failWatcherCreation then
		return nil
	end
	return setmetatable({ callback = callback, userData = userData }, watcherMetatable)
end

function watcherMetatable:element()
	nativeElementLookupCount = nativeElementLookupCount + 1
	return self.nativeElement
end

function watcherMetatable:start(events)
	if not self:element():isApplication() then
		self.watchesElementDestruction = true
	end
	self.events = events
	return self
end

hs = {
	getObjectMetatable = function(objectType)
		if objectType == "hs.application" then
			return applicationMetatable
		end
		assert(objectType == "hs.uielement.watcher")
		return watcherMetatable
	end,
}

local application = setmetatable({}, applicationMetatable)
local startupWatcher
local callback = function() end
local userData = {}
local events = { "AXWindowCreated", "AXFocusedWindowChanged" }
local startupReachedWindowSetup = {}
local originalRequire = require

require = function(moduleName)
	if moduleName == "hs.ipc" then
		return true
	end
	if moduleName == "karabiner_application_focus_variables" then
		return { start = function() end }
	end
	if moduleName == "dock_startup_guard" then
		return {
			allowStartup = function()
				return true
			end,
		}
	end
	if moduleName == "workspace_grid" then
		startupWatcher = application:newWatcher(callback, userData)
		startupWatcher:start(events)
		error(startupReachedWindowSetup)
	end
	return originalRequire(moduleName)
end

local startupSucceeded, startupResult = pcall(dofile, moduleDirectory .. "init.lua")
require = originalRequire
assert(
	not startupSucceeded and startupResult == startupReachedWindowSetup,
	"a failed application lookup must not abort window watcher startup: " .. tostring(startupResult)
)
assert(startupWatcher:element() == application, "an application watcher must keep its original application")
assert(startupWatcher.callback == callback and startupWatcher.userData == userData, "watcher arguments must survive")
assert(startupWatcher.events == events, "the application watcher must start with its requested events")
assert(not startupWatcher.watchesElementDestruction, "application watchers must retain application event semantics")
assert(nativeElementLookupCount == 0, "known applications must not require redundant native PID lookups")

local cache = require("application_watcher_element_cache")
local decoratedNewWatcher = applicationMetatable.newWatcher
local decoratedElement = watcherMetatable.element
cache.install()
assert(applicationMetatable.newWatcher == decoratedNewWatcher, "installing twice must not nest constructor decorators")
assert(watcherMetatable.element == decoratedElement, "installing twice must not nest element decorators")
assert(startupWatcher:element() == application, "installing twice must preserve existing watcher associations")

local window = {
	isApplication = function()
		return false
	end,
}
local windowWatcher = setmetatable({ nativeElement = window }, watcherMetatable)
assert(windowWatcher:element() == window, "window watchers must retain their native element")
assert(windowWatcher:start(events) == windowWatcher, "window watcher startup must retain its return value")
assert(windowWatcher.watchesElementDestruction, "window watchers must still watch element destruction")
assert(nativeElementLookupCount == 2, "each uncached element request must perform exactly one native lookup")

local unresolvedWindowWatcher = setmetatable({}, watcherMetatable)
assert(unresolvedWindowWatcher:element() == nil, "unresolved window elements must not become another application")

failWatcherCreation = true
local creationCountBeforeFailure = nativeWatcherCreationCount
assert(application:newWatcher(callback, userData) == nil, "failed watcher creation must retain the native nil result")
assert(nativeWatcherCreationCount == creationCountBeforeFailure + 1, "failed creation must not introduce retries")
failWatcherCreation = false

local applicationReferences = setmetatable({}, { __mode = "v" })
local watcherReferences = setmetatable({}, { __mode = "v" })
local function createTemporaryApplicationWatcher()
	local temporaryApplication = setmetatable({}, applicationMetatable)
	local temporaryWatcher = temporaryApplication:newWatcher(callback, userData)
	applicationReferences[1] = temporaryApplication
	watcherReferences[1] = temporaryWatcher
	assert(temporaryWatcher:element() == temporaryApplication)
end
createTemporaryApplicationWatcher()
collectgarbage("collect")
collectgarbage("collect")
assert(watcherReferences[1] == nil, "the cache must not retain an otherwise unreachable watcher")
assert(applicationReferences[1] == nil, "the cache must release the application when its watcher is collected")

print("PASS: application lookup failures preserve startup, window watcher semantics, and bounded cache lifetime")
