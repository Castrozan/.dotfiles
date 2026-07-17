-- Bridges the Swift Cmd+Tab window switcher daemon to the Hammerspoon virtual
-- workspaces. The daemon (which renders the card overlay and handles the
-- hold-cmd / cycle / release-to-commit interaction) used to read windows from
-- AeroSpace; now it reads the active workspace's windows from a JSON file this
-- module keeps fresh, and requests focus by writing a window id to a file this
-- module watches. Keeping focus in Hammerspoon avoids the daemon needing its own
-- Accessibility/Screen-Recording grants.

local workspaceGrid = require("workspace_grid")
local pinnedWindow = require("workspace_grid_pinned_window")

local workspaceWindowsFilePath = "/tmp/workspace-window-switcher-windows.json"
local focusRequestFilePath = "/tmp/workspace-window-switcher-focus-request"

local function switchableWindowsOfCurrentWorkspace()
	local currentWorkspaceWindows = workspaceGrid.currentWorkspaceWindowList()
	local switchableWindows = {}
	for _, windowDescriptor in ipairs(currentWorkspaceWindows.windows) do
		if not pinnedWindow.windowTitleIsPinned(windowDescriptor["window-title"]) then
			switchableWindows[#switchableWindows + 1] = windowDescriptor
		end
	end
	return { focused = currentWorkspaceWindows.focused, windows = switchableWindows }
end

local function writeCurrentWorkspaceWindowsFile()
	local serialized = hs.json.encode(switchableWindowsOfCurrentWorkspace())
	local file = io.open(workspaceWindowsFilePath, "w")
	if file then
		file:write(serialized)
		file:close()
	end
end

-- The daemon reads the file when Cmd+Tab activates it; a periodic refresh keeps
-- it current without coupling to every focus/move event.
local windowsFileRefreshTimer = hs.timer.doEvery(1.0, writeCurrentWorkspaceWindowsFile)
windowsFileRefreshTimer:start()

local focusRequestWatcher = hs.pathwatcher.new(focusRequestFilePath, function()
	local file = io.open(focusRequestFilePath, "r")
	if not file then
		return
	end
	local content = file:read("*a") or ""
	file:close()
	local requestedWindowId = tonumber(content:match("^%-?%d+"))
	if requestedWindowId then
		workspaceGrid.focusWindowById(requestedWindowId)
	end
end)
focusRequestWatcher:start()

writeCurrentWorkspaceWindowsFile()

return {
	windowsFileRefreshTimer = windowsFileRefreshTimer,
	focusRequestWatcher = focusRequestWatcher,
}
