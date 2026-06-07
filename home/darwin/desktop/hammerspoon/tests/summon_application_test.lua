local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local offScreenParkingX = -1000000

local launchOrFocusCallCount = 0
local lastLaunchedApplicationName = nil
local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId, isStandardWindow)
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
		currentlyFocusedWindowId = windowId
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

local function makeFakeApplication(windows)
	return {
		mainWindow = function()
			return windows[1]
		end,
		allWindows = function()
			return windows
		end,
		name = function()
			return "Browser"
		end,
	}
end

local runningApplicationsByBundleIdentifier = {}

hs = {
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
			launchOrFocusCallCount = launchOrFocusCallCount + 1
			lastLaunchedApplicationName = applicationName
		end,
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
		filter = {
			default = {
				getWindows = function()
					return {}
				end,
			},
		},
	},
}

local workspaceGrid = require("workspace_grid")

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print(string.format("PASS: %s", description))
	end
end

local runningBrowserWindow = makeFakeWindow(1, true)
runningApplicationsByBundleIdentifier = {
	["com.brave.Browser"] = { makeFakeApplication({ runningBrowserWindow }) },
}
launchOrFocusCallCount = 0
currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser", "com.brave.Browser")

expectEqual("a running browser with a window is not relaunched (no reopen, no extra window)", 0, launchOrFocusCallCount)
expectEqual("the existing browser window is focused", 1, currentlyFocusedWindowId)
expectEqual("the existing browser window is un-parked onto the screen", 0, runningBrowserWindow.storedFrame.x)

runningApplicationsByBundleIdentifier = {
	["com.google.Chrome"] = { makeFakeApplication({}) },
}
launchOrFocusCallCount = 0
lastLaunchedApplicationName = nil
currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Google Chrome", "com.google.Chrome")

expectEqual(
	"a windowless instance (devtools bridge) still triggers a launch to open a window",
	1,
	launchOrFocusCallCount
)
expectEqual("the launch targets the named application", "Google Chrome", lastLaunchedApplicationName)

local windowedInstanceWindow = makeFakeWindow(2, true)
runningApplicationsByBundleIdentifier = {
	["com.google.Chrome"] = {
		makeFakeApplication({}),
		makeFakeApplication({ windowedInstanceWindow }),
	},
}
launchOrFocusCallCount = 0
currentlyFocusedWindowId = nil
workspaceGrid.summonApplicationToCurrentWorkspace("Google Chrome", "com.google.Chrome")

expectEqual("a windowed instance is focused even when a windowless instance also runs", 2, currentlyFocusedWindowId)
expectEqual("no launch happens when any instance already has a window", 0, launchOrFocusCallCount)

os.exit(failureCount == 0 and 0 or 1)
