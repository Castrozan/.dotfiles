local workspaceGridMenuBarReveal = {}

local menuBarVisibleDurationSeconds = 1
local pendingRevealTimer = nil
local pendingHideTimer = nil
local revealedDisplayId = nil
local menuBarVisibilityScript = [=[
ObjC.bindFunction("SLSMainConnectionID", ["int", []]);
ObjC.bindFunction("SLSSetMenuBarVisibilityOverrideOnDisplay", ["int", ["int", "unsigned int", "bool"]]);
$.SLSSetMenuBarVisibilityOverrideOnDisplay($.SLSMainConnectionID(), %d, %s);
]=]

local function setMenuBarVisibility(displayId, visible)
	local succeeded, result, detail =
		hs.osascript.javascript(string.format(menuBarVisibilityScript, displayId, tostring(visible)))
	if not succeeded or result ~= 0 then
		hs.printf("Menu bar visibility failed: %s", tostring(detail or result))
		return false
	end
	return true
end

local function releaseMenuBarVisibility()
	if revealedDisplayId then
		setMenuBarVisibility(revealedDisplayId, false)
		revealedDisplayId = nil
	end
end

local function revealFocusedDisplayMenuBar()
	pendingRevealTimer = nil
	local focusedWindow = hs.window.focusedWindow()
	local screen = (focusedWindow and focusedWindow:screen()) or hs.screen.mainScreen()
	if not screen or not setMenuBarVisibility(screen:id(), true) then
		return
	end
	revealedDisplayId = screen:id()
	pendingHideTimer = hs.timer.doAfter(menuBarVisibleDurationSeconds, function()
		pendingHideTimer = nil
		releaseMenuBarVisibility()
	end)
end

function workspaceGridMenuBarReveal.cancel()
	if pendingRevealTimer then
		pendingRevealTimer:stop()
		pendingRevealTimer = nil
	end
	if pendingHideTimer then
		pendingHideTimer:stop()
		pendingHideTimer = nil
	end
	releaseMenuBarVisibility()
end

function workspaceGridMenuBarReveal.brieflyReveal()
	workspaceGridMenuBarReveal.cancel()
	pendingRevealTimer = hs.timer.doAfter(0, revealFocusedDisplayMenuBar)
end

return workspaceGridMenuBarReveal
