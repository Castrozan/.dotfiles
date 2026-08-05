local workspaceGrid = require("workspace_grid")

local workspaceWindowsFilePath = "/tmp/workspace-window-switcher-windows.json"
local focusRequestFilePath = "/tmp/workspace-window-switcher-focus-request"
local writeCoalescingDelayInSeconds = 0.15

local pendingWriteTimer = nil

local function writeCurrentWorkspaceWindowsFile()
	local serialized = hs.json.encode(workspaceGrid.currentWorkspaceWindowList())
	local file = io.open(workspaceWindowsFilePath, "w")
	if file then
		file:write(serialized)
		file:close()
	end
end

local function scheduleWindowsFileWrite()
	if pendingWriteTimer then
		pendingWriteTimer:stop()
	end
	pendingWriteTimer = hs.timer.doAfter(writeCoalescingDelayInSeconds, function()
		pendingWriteTimer = nil
		writeCurrentWorkspaceWindowsFile()
	end)
end

local windowListChangeEvents = {
	hs.window.filter.windowCreated,
	hs.window.filter.windowDestroyed,
	hs.window.filter.windowFocused,
	hs.window.filter.windowTitleChanged,
}

local windowListChangeWatcher = hs.window.filter.new()
windowListChangeWatcher:subscribe(windowListChangeEvents, scheduleWindowsFileWrite)

workspaceGrid.observeWorkspaceLayoutChanges(scheduleWindowsFileWrite)

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
	windowListChangeWatcher = windowListChangeWatcher,
	focusRequestWatcher = focusRequestWatcher,
	scheduleWindowsFileWrite = scheduleWindowsFileWrite,
	writeCurrentWorkspaceWindowsFile = writeCurrentWorkspaceWindowsFile,
}
