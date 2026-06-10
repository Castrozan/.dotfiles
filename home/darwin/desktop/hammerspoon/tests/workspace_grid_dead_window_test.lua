-- Reproduces the stale-filter-cache bug: hs.window.filter.default keeps
-- returning a window object after its id stops resolving via hs.window.get
-- (a closed window whose destroy event never fired). Operating on that dead
-- object hung the switch loop on an AX setFrame and surfaced it as a phantom
-- "exec" tile in the Cmd+Tab switcher. The grid must skip any window the live
-- lookup no longer resolves.

local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local liveWindowSetFrameCallCount = 0
local deadWindowSetFrameCallCount = 0
local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId, onSetFrame)
  local fakeWindow = { storedFrame = { x = 100, y = 100, w = 400, h = 300 } }
  function fakeWindow:id() return windowId end
  function fakeWindow:isStandard() return true end
  function fakeWindow:frame()
    return { x = self.storedFrame.x, y = self.storedFrame.y, w = self.storedFrame.w, h = self.storedFrame.h }
  end
  function fakeWindow:setFrame(newFrame)
    self.storedFrame = newFrame
    onSetFrame()
  end
  function fakeWindow:screen()
    return { frame = function() return { x = 0, y = 0, w = 1440, h = 900 } end }
  end
  function fakeWindow:focus() currentlyFocusedWindowId = windowId end
  function fakeWindow:application() return { name = function() return "FakeApp" end } end
  function fakeWindow:title() return "fake-title-" .. windowId end
  return fakeWindow
end

local liveWindow = makeFakeWindow(1, function() liveWindowSetFrameCallCount = liveWindowSetFrameCallCount + 1 end)
local deadWindow = makeFakeWindow(99, function() deadWindowSetFrameCallCount = deadWindowSetFrameCallCount + 1 end)

local windowsReturnedByDefaultFilter = { liveWindow, deadWindow }
local function resolveLiveWindowById(targetWindowId)
  if targetWindowId == 1 then return liveWindow end
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
    focusedWindow = function() return resolveLiveWindowById(currentlyFocusedWindowId) end,
    get = function(windowId) return resolveLiveWindowById(windowId) end,
    filter = { default = { getWindows = function() return windowsReturnedByDefaultFilter end } },
  },
}

local workspaceGrid = require("workspace_grid")
require("workspace_grid_persistence").setStateFilePathForTest(os.tmpname())

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
  if expectedValue ~= actualValue then
    failureCount = failureCount + 1
    print(string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue)))
  else
    print(string.format("PASS: %s", description))
  end
end

workspaceGrid.registerExistingWindowsOnFirstWorkspace()
workspaceGrid.switchToWorkspace(2)
workspaceGrid.switchToWorkspace(1)

expectEqual("the dead filter-cache window is never moved (no setFrame, no hang)", 0, deadWindowSetFrameCallCount)
expectEqual("the live window is still laid out across the switches", true, liveWindowSetFrameCallCount > 0)

local windowsOnCurrentWorkspace = workspaceGrid.currentWorkspaceWindowList().windows
expectEqual("only the live window is reported to the switcher (no phantom)", 1, #windowsOnCurrentWorkspace)
expectEqual(
  "the reported window is the live one, not the dead phantom",
  1,
  windowsOnCurrentWorkspace[1] and windowsOnCurrentWorkspace[1]["window-id"] or -1
)

os.exit(failureCount == 0 and 0 or 1)
