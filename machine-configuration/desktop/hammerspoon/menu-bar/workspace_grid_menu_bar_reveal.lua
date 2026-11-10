local workspaceGridMenuBarReveal = {}

local menuBarVisibleDurationSeconds = 1
local scriptRunnerPath = "/usr/bin/osascript"
local menuBarVisibilityScript = [=[
function run(argv) {
	ObjC.bindFunction("SLSMainConnectionID", ["int", []]);
	ObjC.bindFunction("SLSSetMenuBarVisibilityOverrideOnDisplay", ["int", ["int", "unsigned int", "bool"]]);
	return $.SLSSetMenuBarVisibilityOverrideOnDisplay($.SLSMainConnectionID(), parseInt(argv[0]), argv[1] === "true");
}
]=]

local pendingRevealTimer = nil
local pendingHideTimer = nil
local requestedDisplayId = nil
local possiblyVisibleDisplayId = nil
local runningVisibilityCommand = nil
local reconcileMenuBarVisibility

function workspaceGridMenuBarReveal.nextVisibilityCommand(displayIdToReveal, displayIdPossiblyVisible)
	if displayIdToReveal == displayIdPossiblyVisible then
		return nil
	end
	if displayIdPossiblyVisible then
		return { displayId = displayIdPossiblyVisible, visible = false }
	end
	return { displayId = displayIdToReveal, visible = true }
end

local function newVisibilityCommandTask(command, onExit)
	return hs.task.new(scriptRunnerPath, onExit, {
		"-l",
		"JavaScript",
		"-e",
		menuBarVisibilityScript,
		tostring(command.displayId),
		tostring(command.visible),
	})
end

local function finishVisibilityCommand(command, succeeded, failureDetail)
	runningVisibilityCommand = nil
	if not succeeded then
		hs.printf("Menu bar visibility failed: %s", failureDetail)
	end
	if not command.visible then
		possiblyVisibleDisplayId = nil
	elseif not succeeded and requestedDisplayId == command.displayId then
		requestedDisplayId = nil
	end
	reconcileMenuBarVisibility()
end

local function startVisibilityCommand(command)
	local task = newVisibilityCommandTask(command, function(exitCode, standardOutput, standardError)
		local succeeded = exitCode == 0 and tonumber(standardOutput) == 0
		finishVisibilityCommand(command, succeeded, tostring(standardError) .. tostring(standardOutput))
	end)
	if not task or not task:start() then
		finishVisibilityCommand(command, false, "the script runner could not start")
		return
	end
	runningVisibilityCommand = task
	if command.visible then
		possiblyVisibleDisplayId = command.displayId
	end
end

local function hideAfterVisibleDuration()
	pendingHideTimer = hs.timer.doAfter(menuBarVisibleDurationSeconds, function()
		pendingHideTimer = nil
		requestedDisplayId = nil
		reconcileMenuBarVisibility()
	end)
end

reconcileMenuBarVisibility = function()
	if runningVisibilityCommand then
		return
	end
	local command = workspaceGridMenuBarReveal.nextVisibilityCommand(requestedDisplayId, possiblyVisibleDisplayId)
	if command then
		startVisibilityCommand(command)
		return
	end
	if requestedDisplayId and not pendingHideTimer then
		hideAfterVisibleDuration()
	end
end

local function stopPendingTimers()
	if pendingRevealTimer then
		pendingRevealTimer:stop()
		pendingRevealTimer = nil
	end
	if pendingHideTimer then
		pendingHideTimer:stop()
		pendingHideTimer = nil
	end
end

local function requestFocusedDisplayReveal()
	pendingRevealTimer = nil
	local focusedWindow = hs.window.focusedWindow()
	local screen = (focusedWindow and focusedWindow:screen()) or hs.screen.mainScreen()
	requestedDisplayId = screen and screen:id() or nil
	reconcileMenuBarVisibility()
end

function workspaceGridMenuBarReveal.brieflyReveal()
	stopPendingTimers()
	pendingRevealTimer = hs.timer.doAfter(0, requestFocusedDisplayReveal)
end

function workspaceGridMenuBarReveal.releaseBeforeShutdown()
	stopPendingTimers()
	requestedDisplayId = nil
	if runningVisibilityCommand then
		runningVisibilityCommand:setCallback(nil)
		runningVisibilityCommand:waitUntilExit()
		runningVisibilityCommand = nil
	end
	if not possiblyVisibleDisplayId then
		return
	end
	local release = newVisibilityCommandTask({ displayId = possiblyVisibleDisplayId, visible = false }, nil)
	if release and release:start() then
		release:waitUntilExit()
	end
	possiblyVisibleDisplayId = nil
end

return workspaceGridMenuBarReveal
