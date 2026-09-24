local workspaceGridMenuBarReveal = {}

local pendingRevealTimer = nil
local revealTask = nil
local revealRequested = false
local revealTaskCancelled = false

local function launchRequestedReveal()
	if revealTask or not revealRequested then
		return
	end
	revealRequested = false
	local focusedWindow = hs.window.focusedWindow()
	local screen = (focusedWindow and focusedWindow:screen()) or hs.screen.mainScreen()
	if not screen then
		return
	end
	revealTaskCancelled = false
	revealTask = hs.task.new("@MENU_BAR_REVEAL_HELPER@", function(exitCode, _, standardError)
		local wasCancelled = revealTaskCancelled
		revealTask = nil
		revealTaskCancelled = false
		if exitCode ~= 0 and not wasCancelled then
			hs.printf("Menu bar reveal failed (%s): %s", exitCode, standardError)
		end
		launchRequestedReveal()
	end, { tostring(screen:id()) })
	if not revealTask or not revealTask:start() then
		revealTask = nil
		hs.printf("Menu bar reveal helper could not start")
	end
end

function workspaceGridMenuBarReveal.cancel()
	revealRequested = false
	if pendingRevealTimer then
		pendingRevealTimer:stop()
		pendingRevealTimer = nil
	end
	if revealTask and not revealTaskCancelled then
		revealTaskCancelled = true
		revealTask:terminate()
	end
end

function workspaceGridMenuBarReveal.brieflyReveal()
	workspaceGridMenuBarReveal.cancel()
	pendingRevealTimer = hs.timer.doAfter(0, function()
		pendingRevealTimer = nil
		revealRequested = true
		launchRequestedReveal()
	end)
end

return workspaceGridMenuBarReveal
