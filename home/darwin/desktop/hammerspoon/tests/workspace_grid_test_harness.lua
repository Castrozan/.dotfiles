local workspaceGridTestHarness = {}

local currentWindows = {}
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

local function findWindowById(targetWindowId)
	for _, window in ipairs(currentWindows) do
		if window:id() == targetWindowId then
			return window
		end
	end
	return nil
end

function workspaceGridTestHarness.setLiveWindowsToIds(windowIds)
	local rebuiltWindows = {}
	for _, windowId in ipairs(windowIds) do
		table.insert(rebuiltWindows, makeFakeWindow(windowId))
	end
	currentWindows = rebuiltWindows
	currentlyFocusedWindowId = nil
	return rebuiltWindows
end

function workspaceGridTestHarness.installFakeHammerspoonGlobal()
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
			filter = { default = {
				getWindows = function()
					return currentWindows
				end,
			} },
		},
	}
	return hs
end

local stateFile = os.tmpname()
os.remove(stateFile)

function workspaceGridTestHarness.stateFilePath()
	return stateFile
end

function workspaceGridTestHarness.loadFreshGrid()
	package.loaded["workspace_grid"] = nil
	package.loaded["workspace_grid_menubar"] = nil
	package.loaded["workspace_grid_persistence"] = nil
	package.loaded["workspace_grid_window_layout"] = nil
	package.loaded["workspace_grid_window_assignment"] = nil
	package.loaded["workspace_grid_session_generation"] = nil
	package.loaded["workspace_grid_summon"] = nil
	local grid = require("workspace_grid")
	require("workspace_grid_persistence").setStateFilePathForTest(stateFile)
	return grid
end

local failureCount = 0

function workspaceGridTestHarness.expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print(string.format("PASS: %s", description))
	end
end

function workspaceGridTestHarness.exitWithAccumulatedStatus()
	os.exit(failureCount == 0 and 0 or 1)
end

return workspaceGridTestHarness
