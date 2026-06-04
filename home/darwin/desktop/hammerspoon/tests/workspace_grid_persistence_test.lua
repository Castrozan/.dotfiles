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

local windows = { makeFakeWindow(101), makeFakeWindow(102), makeFakeWindow(103) }
local function findWindowById(targetWindowId)
  for _, window in ipairs(windows) do
    if window:id() == targetWindowId then return window end
  end
  return nil
end

hs = {
  menubar = { new = function() return { setTitle = function() end } end },
  styledtext = {
    new = function(text)
      local styledText = { text = text }
      function styledText:setStyle() return self end
      return styledText
    end,
  },
  window = {
    focusedWindow = function() return findWindowById(currentlyFocusedWindowId) end,
    get = function(windowId) return findWindowById(windowId) end,
    filter = { default = { getWindows = function() return windows end } },
  },
}

local stateFile = os.tmpname()
os.remove(stateFile)

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
  if expectedValue ~= actualValue then
    failureCount = failureCount + 1
    print(string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue)))
  else
    print(string.format("PASS: %s", description))
  end
end

local function loadFreshGrid()
  package.loaded["workspace_grid"] = nil
  package.loaded["workspace_grid_menubar"] = nil
  package.loaded["workspace_grid_persistence"] = nil
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

os.exit(failureCount == 0 and 0 or 1)
