local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

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
		}
	end
	function fakeWindow:title()
		return windowTitle
	end
	return fakeWindow
end

local ambientCanvasWindow = makeFakeWindow(1, "ambient-canvas-gpu-screensaver")
local ordinaryWindow = makeFakeWindow(2, "ambient-canvas - Google Chrome - Lucas")
local titlelessPlayerWindow = makeFakeWindow(3, "", "ambient-canvas-player")
local allManagedWindowsInIterationOrder = { ambientCanvasWindow, ordinaryWindow, titlelessPlayerWindow }

local function findWindowById(targetWindowId)
	for _, window in ipairs(allManagedWindowsInIterationOrder) do
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
		allWindows = function()
			return allManagedWindowsInIterationOrder
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

local pinnedWorkspaceNumber = 11

local function windowIsOnWorkspace(windowId, workspaceNumber)
	workspaceGrid.switchToWorkspace(workspaceNumber)
	for _, descriptor in ipairs(workspaceGrid.currentWorkspaceWindowList().windows) do
		if descriptor["window-id"] == windowId then
			return true
		end
	end
	return false
end

workspaceGrid.switchToWorkspace(5)
workspaceGrid.onWindowCreated(ambientCanvasWindow)
expectEqual(
	"created ambient-canvas window pins to workspace 11 despite active workspace 5",
	true,
	windowIsOnWorkspace(1, pinnedWorkspaceNumber)
)
expectEqual("pinned window is absent from the workspace it was created on", false, windowIsOnWorkspace(1, 5))

workspaceGrid.switchToWorkspace(pinnedWorkspaceNumber)
expectEqual(
	"the shown pinned window fills the full display height, covering the menu bar",
	940,
	ambientCanvasWindow.storedFrame.h
)
ambientCanvasWindow:focus()
workspaceGrid.moveFocusedWindowToWorkspace(3)
expectEqual(
	"navigating with the pinned window focused still switches the active workspace",
	3,
	workspaceGrid.currentWorkspaceNumber()
)
expectEqual(
	"cmd-shift move refuses to drag the pinned window off workspace 11",
	true,
	windowIsOnWorkspace(1, pinnedWorkspaceNumber)
)
expectEqual("pinned window never lands on the move destination workspace 3", false, windowIsOnWorkspace(1, 3))

workspaceGrid.switchToWorkspace(3)
workspaceGrid.onWindowCreated(ordinaryWindow)
expectEqual(
	"an ordinary window whose title only starts with ambient-canvas is not pinned to 11",
	false,
	windowIsOnWorkspace(2, pinnedWorkspaceNumber)
)
expectEqual("that ordinary window stays on the workspace it was created on", true, windowIsOnWorkspace(2, 3))

workspaceGrid.switchToWorkspace(5)
workspaceGrid.onWindowCreated(titlelessPlayerWindow)
expectEqual(
	"a player window with no title yet still pins to workspace 11 by application name",
	true,
	windowIsOnWorkspace(3, pinnedWorkspaceNumber)
)
expectEqual("the titleless player window is absent from its creation workspace 5", false, windowIsOnWorkspace(3, 5))

workspaceGrid.switchToWorkspace(3)
workspaceGrid.gatherAllWindowsToCurrentWorkspace()
expectEqual("gather-all leaves the pinned window on workspace 11", true, windowIsOnWorkspace(1, pinnedWorkspaceNumber))
expectEqual("gather-all still pulls an ordinary window onto the current workspace 3", true, windowIsOnWorkspace(2, 3))
expectEqual(
	"an ordinary shown window keeps the working-area height, not the full display",
	900,
	ordinaryWindow.storedFrame.h
)

os.exit(failureCount == 0 and 0 or 1)
