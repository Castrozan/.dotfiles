local workspaceGridSummon = {}

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

function workspaceGridSummon.summon(applicationName, applicationBundleIdentifier, placeWindowOnCurrentWorkspace)
	local window = firstStandardWindowForBundleIdentifier(applicationBundleIdentifier)
	if not window then
		hs.application.launchOrFocus(applicationName)
		return
	end
	placeWindowOnCurrentWorkspace(window)
end

return workspaceGridSummon
