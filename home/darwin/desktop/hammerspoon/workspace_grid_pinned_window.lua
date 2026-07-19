local workspaceGridPinnedWindow = {}

local pinnedWindowWorkspaceNumber = 11
local pinnedWindowTitlePrefixPattern = "^ambient%-canvas%-gpu%-screensaver"
local pinnedWindowApplicationName = "ambient-canvas-player"

function workspaceGridPinnedWindow.windowIsPinned(window)
	if window == nil then
		return false
	end
	local application = window:application()
	if application ~= nil and application:name() == pinnedWindowApplicationName then
		return true
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
