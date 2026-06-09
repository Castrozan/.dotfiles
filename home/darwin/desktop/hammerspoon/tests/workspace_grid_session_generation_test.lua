local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. moduleDirectory .. "tests/?.lua;" .. package.path

local harness = require("workspace_grid_test_harness")
harness.installFakeHammerspoonGlobal()
local expectEqual = harness.expectEqual

local sessionGeneration = require("workspace_grid_session_generation")

local sysctlCommandExecuted = nil
hs.execute = function(command)
	sysctlCommandExecuted = command
	return "FC78F21F-4174-47CF-9A40-D5274802661E\n"
end

local firstTokenRead = sessionGeneration.currentToken()
local secondTokenRead = sessionGeneration.currentToken()

expectEqual(
	"the session token reads the boot-session uuid instead of the drift-prone boot time",
	"sysctl -n kern.bootsessionuuid",
	sysctlCommandExecuted
)
expectEqual("the boot-session token stays stable across reads within one boot", firstTokenRead, secondTokenRead)
expectEqual("the boot-session token is the parsed uuid", "FC78F21F-4174-47CF-9A40-D5274802661E", firstTokenRead)

harness.exitWithAccumulatedStatus()
