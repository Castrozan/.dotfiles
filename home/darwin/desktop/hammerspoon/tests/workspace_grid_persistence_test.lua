local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
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

local windows = { makeFakeWindow(101), makeFakeWindow(102), makeFakeWindow(103) }
local function findWindowById(targetWindowId)
	for _, window in ipairs(windows) do
		if window:id() == targetWindowId then
			return window
		end
	end
	return nil
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
		filter = { default = {
			getWindows = function()
				return windows
			end,
		} },
	},
}

local stateFile = os.tmpname()
os.remove(stateFile)

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

local function loadFreshGrid()
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

local grid = loadFreshGrid()
grid.registerExistingWindowsOnFirstWorkspace()
windows[2]:focus()
grid.moveFocusedWindowToWorkspace(3)
grid.switchToWorkspace(2)
expectEqual("active workspace is 2 before reload", 2, grid.currentWorkspaceNumber())

local reloadedGrid = loadFreshGrid()
reloadedGrid.restorePersistedWorkspaceState()

expectEqual("active workspace 2 survives the reload", 2, reloadedGrid.currentWorkspaceNumber())
reloadedGrid.switchToWorkspace(3)
local windowsOnWorkspaceThree = reloadedGrid.currentWorkspaceWindowList().windows
expectEqual("exactly one window is on workspace 3 after reload", 1, #windowsOnWorkspaceThree)
expectEqual(
	"the window restored onto workspace 3 is 102, not collapsed to workspace 1",
	102,
	windowsOnWorkspaceThree[1] and windowsOnWorkspaceThree[1]["window-id"] or -1
)

windows = { makeFakeWindow(201), makeFakeWindow(202), makeFakeWindow(203) }
currentlyFocusedWindowId = nil

local gridBeforeReboot = loadFreshGrid()
gridBeforeReboot.setSessionGenerationTokenForTest("boot-token-before")
gridBeforeReboot.registerExistingWindowsOnFirstWorkspace()
windows[2]:focus()
gridBeforeReboot.moveFocusedWindowToWorkspace(3)

local gridAfterReboot = loadFreshGrid()
gridAfterReboot.setSessionGenerationTokenForTest("boot-token-after")
gridAfterReboot.restorePersistedWorkspaceState()
expectEqual("after a reboot the active workspace resets to 1", 1, gridAfterReboot.currentWorkspaceNumber())
gridAfterReboot.registerExistingWindowsOnFirstWorkspace()
gridAfterReboot.switchToWorkspace(3)
expectEqual(
	"after a reboot no window resurrects on workspace 3 from the stale map",
	0,
	#gridAfterReboot.currentWorkspaceWindowList().windows
)

windows = { makeFakeWindow(301), makeFakeWindow(302) }
currentlyFocusedWindowId = nil

local gridWithBothWindows = loadFreshGrid()
gridWithBothWindows.setSessionGenerationTokenForTest("boot-token-stable")
gridWithBothWindows.registerExistingWindowsOnFirstWorkspace()
windows[2]:focus()
gridWithBothWindows.moveFocusedWindowToWorkspace(3)

windows = { makeFakeWindow(301) }
currentlyFocusedWindowId = nil

local gridAfterWindowClosed = loadFreshGrid()
gridAfterWindowClosed.setSessionGenerationTokenForTest("boot-token-stable")
gridAfterWindowClosed.restorePersistedWorkspaceState()
gridAfterWindowClosed.switchToWorkspace(3)
expectEqual(
	"a window that closed while unobserved does not resurrect on workspace 3 via recycled id",
	0,
	#gridAfterWindowClosed.currentWorkspaceWindowList().windows
)

os.exit(failureCount == 0 and 0 or 1)
