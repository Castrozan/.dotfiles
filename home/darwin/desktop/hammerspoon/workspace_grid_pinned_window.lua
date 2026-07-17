local workspaceGridPinnedWindow = {}

local pinnedWindowWorkspaceNumber = 11
local pinnedWindowTitlePrefixPattern = "^ambient%-canvas%-gpu%-screensaver"

function workspaceGridPinnedWindow.windowTitleIsPinned(windowTitle)
	return windowTitle ~= nil and windowTitle:match(pinnedWindowTitlePrefixPattern) ~= nil
end

function workspaceGridPinnedWindow.windowIsPinned(window)
	if window == nil then
		return false
	end
	return workspaceGridPinnedWindow.windowTitleIsPinned(window:title())
end

function workspaceGridPinnedWindow.resolveWorkspaceForWindow(window, fallbackWorkspaceNumber)
	if workspaceGridPinnedWindow.windowIsPinned(window) then
		return pinnedWindowWorkspaceNumber
	end
	return fallbackWorkspaceNumber
end

return workspaceGridPinnedWindow
