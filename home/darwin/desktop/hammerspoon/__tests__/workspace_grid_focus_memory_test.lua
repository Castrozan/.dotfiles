-- Reproduces the workspace-switch focus-memory bug: navigating away from a
-- workspace and back must restore the window that was last focused on THAT
-- workspace, and each workspace must remember its own focus independently,
-- instead of grabbing an arbitrary window in iteration order.

local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId)
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
		}
	end
	function fakeWindow:focus()
		currentlyFocusedWindowId = windowId
	end
	function fakeWindow:application()
		return {
			name = function()
				return "FakeApp"
			end,
		}
	end
	function fakeWindow:title()
		return "fake-title-" .. windowId
	end
	return fakeWindow
end

local windowA = makeFakeWindow(1)
local windowB = makeFakeWindow(2)
local windowC = makeFakeWindow(3)
local allWindows = { windowA, windowB, windowC }

local function findWindowById(targetWindowId)
	for _, window in ipairs(allWindows) do
		if window:id() == targetWindowId then
			return window
		end
	end
	return nil
end

hs = {
  menubar = { new = function() return { setTitle = function() end } end },
  styledtext = {
    new = function(text)
      return setmetatable({ text = text }, {
        __concat = function(left, right) return hs.styledtext.new(left.text .. right.text) end,
      })
    end,
  },
  window = {
    focusedWindow = function() return findWindowById(currentlyFocusedWindowId) end,
    get = function(windowId) return findWindowById(windowId) end,
    allWindows = function() return allWindows end,
    filter = { default = { getWindows = function() return allWindows end } },
  },
}

local workspaceGrid = require("workspace_grid")
require("workspace_grid_persistence").setStateFilePathForTest(os.tmpname())

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

workspaceGrid.registerExistingWindowsOnDefaultWorkspace()

windowC:focus()
workspaceGrid.moveFocusedWindowToWorkspace(2)
workspaceGrid.switchToWorkspace(11)

windowB:focus()
workspaceGrid.onWindowFocused(windowB)

workspaceGrid.switchToWorkspace(2)
expectEqual("returning to workspace 2 restores its last-focused window C", 3, currentlyFocusedWindowId)

workspaceGrid.switchToWorkspace(11)
expectEqual("returning to workspace 11 restores last-focused B, not iteration-order A", 2, currentlyFocusedWindowId)

windowB:focus()
workspaceGrid.onWindowFocused(windowB)
local preservedFocusOnReload = workspaceGrid.switchToWorkspace(11, hs.window.focusedWindow())
expectEqual("a reload re-entering the current workspace keeps the live focused window", 2, currentlyFocusedWindowId)

os.exit(failureCount == 0 and 0 or 1)
