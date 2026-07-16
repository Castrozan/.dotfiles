local workspaceGridSummon = {}

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
