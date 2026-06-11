-- Reproduces the move-window-with-me focus-handoff bug: moving the focused
-- window into a workspace that already contains another window must leave the
-- moved window focused, so a subsequent ctrl-alt-shift carries the SAME window
-- onward instead of grabbing the pre-existing window on the intermediate space.

local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId, isStandardWindow)
  local fakeWindow = {
    storedFrame = { x = 100, y = 100, w = 400, h = 300 },
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
    return { name = function() return "FakeApp" end }
  end
  function fakeWindow:title()
    return "fake-title-" .. windowId
  end
  return fakeWindow
end

local windowA = makeFakeWindow(1, true)
local windowB = makeFakeWindow(2, true)
local allManagedWindowsInIterationOrder = { windowA, windowB }

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
    print(string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue)))
  else
    print(string.format("PASS: %s", description))
  end
end

windowB:focus()
workspaceGrid.moveFocusedWindowToWorkspace(2)
workspaceGrid.switchToWorkspace(1)
windowA:focus()

workspaceGrid.moveFocusedWindowToWorkspace(2)
expectEqual("moved window A keeps focus on the destination workspace with a resident window", 1, currentlyFocusedWindowId)

workspaceGrid.moveFocusedWindowToWorkspace(3)
expectEqual("second move carries the same window A onward, not the resident window B", 1, currentlyFocusedWindowId)
local windowsNowOnWorkspaceThree = workspaceGrid.currentWorkspaceWindowList().windows
expectEqual("exactly one window lands on workspace 3", 1, #windowsNowOnWorkspaceThree)
expectEqual("the window on workspace 3 is the one we carried (A), not the resident (B)", 1, windowsNowOnWorkspaceThree[1] and windowsNowOnWorkspaceThree[1]["window-id"] or -1)

os.exit(failureCount == 0 and 0 or 1)
