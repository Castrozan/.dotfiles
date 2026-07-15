local workspaceGridSummon = {}

local terminationPollIntervalSeconds = 0.1
local terminationPollMaximumAttempts = 50

local windowlessInstanceRelaunchInProgressByBundleIdentifier = {}
local pendingRelaunchTimerByBundleIdentifier = {}

local function firstStandardWindowForBundleIdentifier(applicationBundleIdentifier)
	for _, application in ipairs(hs.application.applicationsForBundleID(applicationBundleIdentifier)) do
		local mainWindow = application:mainWindow()
		if mainWindow and mainWindow:isStandard() then
			return mainWindow
		end
		for _, window in ipairs(application:allWindows()) do
			if window:isStandard() then
				return window
			end
		end
	end
	return nil
end

local function firstStandardWindowMatchingProfileForBundleIdentifier(applicationBundleIdentifier, windowMatchesProfile)
	for _, application in ipairs(hs.application.applicationsForBundleID(applicationBundleIdentifier)) do
		for _, window in ipairs(application:allWindows()) do
			if window:isStandard() and windowMatchesProfile(window) then
				return window
			end
		end
	end
	return nil
end

local function anyRunningInstanceHasAnyWindow(runningApplications)
	for _, application in ipairs(runningApplications) do
		if #application:allWindows() > 0 then
			return true
		end
	end
	return false
end

local function finishRelaunch(applicationName, applicationBundleIdentifier)
	local pendingTimer = pendingRelaunchTimerByBundleIdentifier[applicationBundleIdentifier]
	if pendingTimer then
		pendingTimer:stop()
	end
	pendingRelaunchTimerByBundleIdentifier[applicationBundleIdentifier] = nil
	windowlessInstanceRelaunchInProgressByBundleIdentifier[applicationBundleIdentifier] = nil
	hs.application.launchOrFocus(applicationName)
end

local function quitWindowlessInstancesThenRelaunchToRestoreSession(
	runningApplications,
	applicationName,
	applicationBundleIdentifier
)
	if windowlessInstanceRelaunchInProgressByBundleIdentifier[applicationBundleIdentifier] then
		return
	end
	windowlessInstanceRelaunchInProgressByBundleIdentifier[applicationBundleIdentifier] = true
	for _, application in ipairs(runningApplications) do
		application:kill()
	end
	local remainingTerminationPollAttempts = terminationPollMaximumAttempts
	pendingRelaunchTimerByBundleIdentifier[applicationBundleIdentifier] = hs.timer.doEvery(
		terminationPollIntervalSeconds,
		function()
			remainingTerminationPollAttempts = remainingTerminationPollAttempts - 1
			local applicationHasFullyTerminated = #hs.application.applicationsForBundleID(
					applicationBundleIdentifier
				) == 0
			if applicationHasFullyTerminated or remainingTerminationPollAttempts <= 0 then
				finishRelaunch(applicationName, applicationBundleIdentifier)
			end
		end
	)
end

function workspaceGridSummon.summon(
	applicationName,
	applicationBundleIdentifier,
	placeWindowOnCurrentWorkspace,
	coldLaunchShellCommand
)
	local standardWindow = firstStandardWindowForBundleIdentifier(applicationBundleIdentifier)
	if standardWindow then
		placeWindowOnCurrentWorkspace(standardWindow)
		return
	end
	if coldLaunchShellCommand then
		hs.execute(coldLaunchShellCommand, true)
		return
	end
	local runningApplications = hs.application.applicationsForBundleID(applicationBundleIdentifier)
	if #runningApplications == 0 or anyRunningInstanceHasAnyWindow(runningApplications) then
		hs.application.launchOrFocus(applicationName)
		return
	end
	quitWindowlessInstancesThenRelaunchToRestoreSession(
		runningApplications,
		applicationName,
		applicationBundleIdentifier
	)
end

function workspaceGridSummon.summonProfileWindow(
	applicationBundleIdentifier,
	placeWindowOnCurrentWorkspace,
	coldLaunchShellCommand,
	windowMatchesProfile
)
	local profileWindow =
		firstStandardWindowMatchingProfileForBundleIdentifier(applicationBundleIdentifier, windowMatchesProfile)
	if profileWindow then
		placeWindowOnCurrentWorkspace(profileWindow)
		return
	end
	hs.execute(coldLaunchShellCommand, true)
end

return workspaceGridSummon
