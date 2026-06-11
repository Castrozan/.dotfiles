-- Verifies the gather escape hatch: a single command must reclaim every live
-- window onto the current workspace and lay each one back on-screen, so windows
-- stranded on a hotkey-less workspace are always recoverable.

local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local currentlyFocusedWindowId = nil

local function makeFakeWindow(windowId)
  local fakeWindow = { storedFrame = { x = 100, y = 100, w = 400, h = 300 } }
  function fakeWindow:id() return windowId end
  function fakeWindow:isStandard() return true end
  function fakeWindow:frame()
    return { x = self.storedFrame.x, y = self.storedFrame.y, w = self.storedFrame.w, h = self.storedFrame.h }
  end
  function fakeWindow:setFrame(newFrame) self.storedFrame = newFrame end
  function fakeWindow:screen()
    return { frame = function() return { x = 0, y = 0, w = 1440, h = 900 } end }
  end
  function fakeWindow:focus() currentlyFocusedWindowId = windowId end
  function fakeWindow:application() return { name = function() return "FakeApp" end } end
  function fakeWindow:title() return "fake-title-" .. windowId end
  return fakeWindow
end

local windowA = makeFakeWindow(1)
local windowB = makeFakeWindow(2)
local windowC = makeFakeWindow(3)
local allWindows = { windowA, windowB, windowC }

local function findWindowById(targetWindowId)
  for _, window in ipairs(allWindows) do
    if window:id() == targetWindowId then return window end
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
    print(string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue)))
  else
    print(string.format("PASS: %s", description))
  end
end

workspaceGrid.registerExistingWindowsOnFirstWorkspace()
windowA:focus()
workspaceGrid.moveFocusedWindowToWorkspace(2)
workspaceGrid.switchToWorkspace(3)

workspaceGrid.gatherAllWindowsToCurrentWorkspace()

local windowsOnWorkspaceThree = workspaceGrid.currentWorkspaceWindowList().windows
expectEqual("gather reclaims all three windows onto the current workspace", 3, #windowsOnWorkspaceThree)
expectEqual("gathered window A is laid back on-screen", 0, windowA.storedFrame.x)
expectEqual("gathered window B is laid back on-screen", 0, windowB.storedFrame.x)
expectEqual("gathered window C is laid back on-screen", 0, windowC.storedFrame.x)

os.exit(failureCount == 0 and 0 or 1)
