local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId, windowTitle, applicationName)
	local resolvedApplicationName = applicationName or "FakeApp"
	local fakeWindow = { storedFrame = { x = 100, y = 100, w = 400, h = 300 } }
	function fakeWindow:id()
		return windowId
	end
	function fakeWindow:isStandard()
		return true
	end
	function fakeWindow:frame()
		return { x = self.storedFrame.x, y = self.storedFrame.y, w = self.storedFrame.w, h = self.storedFrame.h }
	end
	function fakeWindow:setFrame(newFrame)
		self.storedFrame = newFrame
	end
	function fakeWindow:screen()
		return {
			frame = function()
				return { x = 0, y = 0, w = 1440, h = 900 }
			end,
			fullFrame = function()
				return { x = 0, y = 0, w = 1440, h = 940 }
			end,
		}
	end
	function fakeWindow:focus()
		currentlyFocusedWindowId = windowId
	end
	function fakeWindow:application()
		return {
			name = function()
				return resolvedApplicationName
			end,
			bundleID = function()
				return "com.example.fakeapp"
			end,
		}
	end
	function fakeWindow:title()
		return windowTitle
	end
	return fakeWindow
end

local ambientCanvasWindow = makeFakeWindow(1, "ambient-canvas-gpu-screensaver")
local ordinaryWindow = makeFakeWindow(2, "ambient-canvas - Google Chrome - Lucas")
local titlelessPlayerWindow = makeFakeWindow(3, "", "ᓚᘏᗢ")
local allManagedWindowsInIterationOrder = { ambientCanvasWindow, ordinaryWindow, titlelessPlayerWindow }

local function findWindowById(targetWindowId)
	for _, window in ipairs(allManagedWindowsInIterationOrder) do
		if window:id() == targetWindowId then
			return window
		end
	end
	return nil
end

local function windowServerEntriesForWindows(windows)
	local windowServerEntries = {}
	for _, window in ipairs(windows) do
		windowServerEntries[#windowServerEntries + 1] = { kCGWindowNumber = window:id() }
	end
	return windowServerEntries
end

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
	window = {
		focusedWindow = function()
			return findWindowById(currentlyFocusedWindowId)
		end,
		get = function(windowId)
			return findWindowById(windowId)
		end,
		list = function()
			return windowServerEntriesForWindows(allManagedWindowsInIterationOrder)
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
package.loaded["workspace_grid_menu_bar_reveal"] = { brieflyReveal = function() end }
local workspaceGrid = require("workspace_grid")
require("workspace_grid_persistence").setStateFilePathForTest(os.tmpname())

return {
	workspaceGrid = workspaceGrid,
	ambientCanvasWindow = ambientCanvasWindow,
	ordinaryWindow = ordinaryWindow,
	titlelessPlayerWindow = titlelessPlayerWindow,
}
