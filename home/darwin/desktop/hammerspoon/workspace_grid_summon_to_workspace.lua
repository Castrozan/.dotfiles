local windowSummon = require("workspace_grid_summon")

local function buildSummonToWorkspaceEntryPoints(placeWindowOnCurrentWorkspace)
	local entryPoints = {}

	function entryPoints.summonApplicationToCurrentWorkspace(
		applicationName,
		applicationBundleIdentifier,
		coldLaunchShellCommand
	)
		windowSummon.summon(
			applicationName,
			applicationBundleIdentifier,
			placeWindowOnCurrentWorkspace,
			coldLaunchShellCommand
		)
	end

	function entryPoints.summonApplicationProfileWindowToCurrentWorkspace(
		applicationBundleIdentifier,
		coldLaunchShellCommand,
		windowMatchesProfile
	)
		windowSummon.summonProfileWindow(
			applicationBundleIdentifier,
			placeWindowOnCurrentWorkspace,
			coldLaunchShellCommand,
			windowMatchesProfile
		)
	end

	return entryPoints
end

return { buildSummonToWorkspaceEntryPoints = buildSummonToWorkspaceEntryPoints }
