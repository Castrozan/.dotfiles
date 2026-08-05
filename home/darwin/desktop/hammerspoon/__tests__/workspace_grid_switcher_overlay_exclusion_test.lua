local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local switcherOverlayOwnerNameAsTheWindowServerTruncatesIt = "workspace-window-switcher-daemo"

local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId, applicationName, isStandardWindow)
	local fakeWindow = { storedFrame = { x = 100, y = 100, w = 400, h = 300 } }
	function fakeWindow:id()
		return windowId
	end
	function fakeWindow:isStandard()
		return isStandardWindow
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
				return applicationName
			end,
			bundleID = function()
				return "com.example." .. applicationName
			end,
		}
	end
	function fakeWindow:title()
		return ""
	end
	return fakeWindow
end

local editorWindow = makeFakeWindow(701, "WezTerm", true)
local browserWindow = makeFakeWindow(702, "Google Chrome", true)
local switcherOverlayWindow = makeFakeWindow(703, "workspace-window-switcher-daemon", false)

local windowsTheFilterReports = { editorWindow, browserWindow, switcherOverlayWindow }
local windowServerEntries = {
	{ kCGWindowNumber = 701, kCGWindowOwnerName = "WezTerm", kCGWindowLayer = 0 },
	{ kCGWindowNumber = 702, kCGWindowOwnerName = "Google Chrome", kCGWindowLayer = 0 },
	{
		kCGWindowNumber = 703,
		kCGWindowOwnerName = switcherOverlayOwnerNameAsTheWindowServerTruncatesIt,
		kCGWindowLayer = 101,
	},
}

local function findWindowById(targetWindowId)
	for _, window in ipairs(windowsTheFilterReports) do
		if window:id() == targetWindowId then
			return window
		end
	end
	return nil
end

hs = {
	menubar = {
		new = function()
			return { setTitle = function() end, setMenu = function() end }
		end,
	},
	image = {
		imageFromAppBundle = function()
			return nil
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
		list = function()
			return windowServerEntries
		end,
		filter = {
			default = {
				getWindows = function()
					return windowsTheFilterReports
				end,
			},
		},
	},
}

local workspaceGrid = require("workspace_grid")
require("workspace_grid_persistence").setStateFilePathForTest(os.tmpname())
local windowQuery = require("workspace_grid_window_query")

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
workspaceGrid.switchToWorkspace(11)

local function windowIdsIn(windowList)
	local ids = {}
	for _, window in ipairs(windowList) do
		ids[window["window-id"] or window:id()] = true
	end
	return ids
end

local reportedToTheSwitcher = windowIdsIn(workspaceGrid.currentWorkspaceWindowList().windows)
expectEqual(
	"the switcher's own overlay panel is never offered back to the switcher as a card",
	nil,
	reportedToTheSwitcher[703]
)
expectEqual("the terminal window is still offered", true, reportedToTheSwitcher[701])
expectEqual("the browser window is still offered", true, reportedToTheSwitcher[702])

local manageable = windowIdsIn(windowQuery.manageableWindows())
expectEqual("the switcher's own overlay panel is not a manageable window", nil, manageable[703])
expectEqual("the terminal window is still manageable", true, manageable[701])

expectEqual(
	"the switcher's own overlay panel does not resolve as a focus target",
	nil,
	windowQuery.manageableWindowById(703)
)

expectEqual(
	"the window menu never lists the switcher's own overlay panel",
	nil,
	windowIdsIn(require("workspace_grid_window_snapshot").captureSnapshot().descriptorsByWorkspaceNumber[11] or {})[703]
)

os.exit(failureCount == 0 and 0 or 1)
