local workspaceGridPinnedWindow = {}

local pinnedWindowWorkspaceNumber = 11
local pinnedWindowTitlePrefixPattern = "^ambient%-canvas"

function workspaceGridPinnedWindow.windowIsPinned(window)
	if window == nil then
		return false
	end
	local windowTitle = window:title()
	return windowTitle ~= nil and windowTitle:match(pinnedWindowTitlePrefixPattern) ~= nil
end

function workspaceGridPinnedWindow.resolveWorkspaceForWindow(window, fallbackWorkspaceNumber)
	if workspaceGridPinnedWindow.windowIsPinned(window) then
		return pinnedWindowWorkspaceNumber
	end
	return fallbackWorkspaceNumber
end

return workspaceGridPinnedWindow
