local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "__tests__/?.lua;" .. package.path

local harness = require("summon_test_harness")
local expectEqual = harness.expectEqual
local weztermSummon = require("wezterm_summon")
local invocation = {}
local workspaceGrid = {}

function workspaceGrid.summonApplicationProfileWindowToCurrentWorkspace(
	applicationBundleIdentifier,
	coldLaunchShellCommand,
	windowMatchesProfile
)
	invocation.applicationBundleIdentifier = applicationBundleIdentifier
	invocation.coldLaunchShellCommand = coldLaunchShellCommand
	invocation.windowMatchesProfile = windowMatchesProfile
end

weztermSummon.summonToCurrentWorkspace(workspaceGrid)

expectEqual(
	"WezTerm is selected by its bundle identifier",
	"com.github.wez.wezterm",
	invocation.applicationBundleIdentifier
)
expectEqual(
	"a missing WezTerm window launches the application",
	"/usr/bin/open -a WezTerm",
	invocation.coldLaunchShellCommand
)
expectEqual("every standard WezTerm window matches", true, invocation.windowMatchesProfile({}))

harness.exitWithAccumulatedResult()
