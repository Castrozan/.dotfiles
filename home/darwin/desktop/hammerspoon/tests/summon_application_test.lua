-- Reproduces the Cmd+B double-window bug: summoning an already-running browser
-- must NOT call launchOrFocus, because launchOrFocus reopens the app and Chromium
-- answers the reopen by spawning a fresh window on top of the one we summon.
-- It must only re-tag, un-park, and focus the existing window.

local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local offScreenParkingX = -1000000

local launchOrFocusCallCount = 0
local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId)
	local fakeWindow = {
		storedFrame = { x = offScreenParkingX, y = 100, w = 400, h = 300 },
	}
	function fakeWindow:id()
		return windowId
	end
	function fakeWindow:isStandard()
		return true
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
				return "Brave Browser"
			end,
		}
	end
	function fakeWindow:title()
		return "fake-title-" .. windowId
	end
	return fakeWindow
end

local braveWindow = makeFakeWindow(1)
local allManagedWindowsInIterationOrder = { braveWindow }

local function findWindowById(targetWindowId)
	for _, window in ipairs(allManagedWindowsInIterationOrder) do
		if window:id() == targetWindowId then
			return window
		end
	end
	return nil
end

local fakeBraveApplication = {
	mainWindow = function()
		return braveWindow
	end,
	allWindows = function()
		return { braveWindow }
	end,
	name = function()
		return "Brave Browser"
	end,
}

hs = {
	menubar = {
		new = function()
			return { setIcon = function() end }
		end,
	},
	canvas = {
		new = function()
			return {
				replaceElements = function() end,
				imageFromCanvas = function() return {} end,
				delete = function() end,
			}
		end,
	},
	application = {
		launchOrFocus = function()
			launchOrFocusCallCount = launchOrFocusCallCount + 1
		end,
		get = function(applicationName)
			if applicationName == "Brave Browser" then
				return fakeBraveApplication
			end
			return nil
		end,
	},
	window = {
		focusedWindow = function()
			return findWindowById(currentlyFocusedWindowId)
		end,
		get = function(windowId)
			return findWindowById(windowId)
		end,
		filter = {
			default = {
				getWindows = function()
					return allManagedWindowsInIterationOrder
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

workspaceGrid.summonApplicationToCurrentWorkspace("Brave Browser")

expectEqual("already-running Brave is not relaunched (no reopen, no extra window)", 0, launchOrFocusCallCount)
expectEqual("the existing Brave window is focused", 1, currentlyFocusedWindowId)
expectEqual("the existing Brave window is un-parked onto the screen", 0, braveWindow.storedFrame.x)

os.exit(failureCount == 0 and 0 or 1)
