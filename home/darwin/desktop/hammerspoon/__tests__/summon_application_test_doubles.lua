local summonApplicationTestDoubles = {}

local offScreenParkingX = -1000000
summonApplicationTestDoubles.offScreenParkingX = offScreenParkingX

local captures = {
	currentlyFocusedWindowId = nil,
	lastExecuteRanInUserEnvironment = nil,
	executedShellCommands = {},
}
summonApplicationTestDoubles.captures = captures

local runningApplicationsByBundleIdentifier = {}
function summonApplicationTestDoubles.setRunningApplications(applicationsByBundleIdentifier)
	runningApplicationsByBundleIdentifier = applicationsByBundleIdentifier
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
	return {
		allWindows = function()
			return windows
		end,
		name = function()
			return "Browser"
		end,
	}
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
			applicationsForBundleID = function(bundleIdentifier)
				return runningApplicationsByBundleIdentifier[bundleIdentifier] or {}
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
