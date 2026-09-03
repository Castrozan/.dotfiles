local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local createdHotkeys = {}

hs = {
	hotkey = {
		new = function(modifiers, key, callback)
			local hotkey = {
				modifiers = modifiers,
				key = key,
				callback = callback,
				enabled = false,
			}
			function hotkey:enable()
				self.enabled = true
			end
			function hotkey:disable()
				self.enabled = false
			end
			table.insert(createdHotkeys, hotkey)
			return hotkey
		end,
	},
}

local tilingActive = false
local layoutObserver = nil
local leftFocusCount = 0
local rightFocusCount = 0
local grid = {
	focusLeftTiledWindow = function()
		leftFocusCount = leftFocusCount + 1
	end,
	focusRightTiledWindow = function()
		rightFocusCount = rightFocusCount + 1
	end,
	twoWindowTilingIsActive = function()
		return tilingActive
	end,
	observeWorkspaceLayoutChanges = function(observer)
		layoutObserver = observer
	end,
}

require("workspace_grid_two_window_tiling_hotkeys").install(grid)

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print(string.format("PASS: %s", description))
	end
end

expectEqual("only the two directional hotkeys are installed", 2, #createdHotkeys)
expectEqual("the left hotkey uses Cmd+Left", "cmd:left", createdHotkeys[1].modifiers[1] .. ":" .. createdHotkeys[1].key)
expectEqual(
	"the right hotkey uses Cmd+Right",
	"cmd:right",
	createdHotkeys[2].modifiers[1] .. ":" .. createdHotkeys[2].key
)
expectEqual("Cmd+Left starts disabled in accordion mode", false, createdHotkeys[1].enabled)
expectEqual("Cmd+Right starts disabled in accordion mode", false, createdHotkeys[2].enabled)

tilingActive = true
layoutObserver()
expectEqual("Cmd+Left is enabled while the pair is active", true, createdHotkeys[1].enabled)
expectEqual("Cmd+Right is enabled while the pair is active", true, createdHotkeys[2].enabled)
createdHotkeys[1].callback()
createdHotkeys[2].callback()
expectEqual("Cmd+Left routes to the left member", 1, leftFocusCount)
expectEqual("Cmd+Right routes to the right member", 1, rightFocusCount)

tilingActive = false
layoutObserver()
expectEqual("Cmd+Left is disabled after restoring accordion mode", false, createdHotkeys[1].enabled)
expectEqual("Cmd+Right is disabled after restoring accordion mode", false, createdHotkeys[2].enabled)

os.exit(failureCount == 0 and 0 or 1)
