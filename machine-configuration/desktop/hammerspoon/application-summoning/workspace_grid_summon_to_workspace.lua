local windowSummon = require("workspace_grid_summon")

local function buildSummonToWorkspaceEntryPoints(placeWindowOnCurrentWorkspace)
	local entryPoints = {}

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
