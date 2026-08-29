local weztermSummon = {}

function weztermSummon.summonToCurrentWorkspace(workspaceGrid)
	workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace(
		"com.github.wez.wezterm",
		"/usr/bin/open -a WezTerm",
		function()
			return true
		end
	)
end

return weztermSummon
