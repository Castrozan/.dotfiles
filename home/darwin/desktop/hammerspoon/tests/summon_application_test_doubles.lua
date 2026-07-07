local summonApplicationTestDoubles = {}

local offScreenParkingX = -1000000
summonApplicationTestDoubles.offScreenParkingX = offScreenParkingX

local captures = {
	launchOrFocusCallCount = 0,
	lastLaunchedApplicationName = nil,
	currentlyFocusedWindowId = nil,
	lastExecuteRanInUserEnvironment = nil,
	executedShellCommands = {},
	killCallCount = 0,
	deferTerminationAndRelaunch = false,
	pendingRelaunchActions = {},
}
summonApplicationTestDoubles.captures = captures

local runningApplicationsByBundleIdentifier = {}
function summonApplicationTestDoubles.setRunningApplications(applicationsByBundleIdentifier)
	runningApplicationsByBundleIdentifier = applicationsByBundleIdentifier
end

function summonApplicationTestDoubles.finishPendingTerminations()
	for _, applications in pairs(runningApplicationsByBundleIdentifier) do
		for _, application in ipairs(applications) do
			if application.terminationRequested then
				application.terminated = true
			end
		end
	end
end

function summonApplicationTestDoubles.runPendingRelaunchActions()
	local pendingActions = captures.pendingRelaunchActions
	captures.pendingRelaunchActions = {}
	for _, pendingAction in ipairs(pendingActions) do
		pendingAction()
	end
end

function summonApplicationTestDoubles.makeFakeWindow(windowId, isStandardWindow)
	local fakeWindow = {
		storedFrame = { x = offScreenParkingX, y = 100, w = 400, h = 300 },
	}
	function fakeWindow:id()
		return windowId
	end
	function fakeWindow:isStandard()
		return isStandardWindow
	end
	function fakeWindow:frame()
		return {
			x = self.storedFrame.x,
			y = self.storedFrame.y,
			w = self.storedFrame.w,
			h = self.storedFrame.h,
		}
	end
	function fakeWindow:setFrame(newFrame)
		self.storedFrame = newFrame
	end
	function fakeWindow:screen()
		return {
			frame = function()
				return { x = 0, y = 0, w = 1440, h = 900 }
			end,
		}
	end
	function fakeWindow:focus()
		captures.currentlyFocusedWindowId = windowId
	end
	function fakeWindow:application()
		return {
			name = function()
				return "Browser"
			end,
		}
	end
	function fakeWindow:title()
		return "fake-title-" .. windowId
	end
	return fakeWindow
end

function summonApplicationTestDoubles.makeFakeApplication(windows)
	local fakeApplication = {
		mainWindow = function()
			return windows[1]
		end,
		allWindows = function()
			return windows
		end,
		name = function()
			return "Browser"
		end,
		terminated = false,
		terminationRequested = false,
	}
	function fakeApplication:kill()
		captures.killCallCount = captures.killCallCount + 1
		fakeApplication.terminationRequested = true
		if not captures.deferTerminationAndRelaunch then
			fakeApplication.terminated = true
		end
	end
	return fakeApplication
end

function summonApplicationTestDoubles.installGlobalHammerspoonMock()
	hs = {
		execute = function(command, withUserEnvironment)
			captures.lastExecuteRanInUserEnvironment = withUserEnvironment
			table.insert(captures.executedShellCommands, command)
		end,
		menubar = {
			new = function()
				return { setTitle = function() end }
			end,
		},
		styledtext = {
			new = function(text)
				return setmetatable({ text = text }, {
					__concat = function(left, right)
						return hs.styledtext.new(left.text .. right.text)
					end,
				})
			end,
		},
		application = {
			launchOrFocus = function(applicationName)
				captures.launchOrFocusCallCount = captures.launchOrFocusCallCount + 1
				captures.lastLaunchedApplicationName = applicationName
			end,
			applicationsForBundleID = function(bundleIdentifier)
				local applications = runningApplicationsByBundleIdentifier[bundleIdentifier] or {}
				local aliveApplications = {}
				for _, application in ipairs(applications) do
					if not application.terminated then
						table.insert(aliveApplications, application)
					end
				end
				return aliveApplications
			end,
		},
		timer = {
			doEvery = function(_, tickFunction)
				local timerObject = { stopped = false }
				function timerObject:stop()
					self.stopped = true
				end
				local guardedTick = function()
					if not timerObject.stopped then
						tickFunction()
					end
				end
				if captures.deferTerminationAndRelaunch then
					table.insert(captures.pendingRelaunchActions, guardedTick)
				else
					guardedTick()
				end
				return timerObject
			end,
		},
		window = {
			focusedWindow = function()
				return nil
			end,
			get = function()
				return nil
			end,
			allWindows = function()
				return {}
			end,
			filter = {
				default = {
					getWindows = function()
						return {}
					end,
				},
			},
		},
	}
end

return summonApplicationTestDoubles
