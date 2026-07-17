local moduleDirectory = arg[0]:gsub("tests/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local capturedSwitcherFeeds = {}
local realIoOpen = io.open
io.open = function(path, mode)
	if path == "/tmp/workspace-window-switcher-windows.json" and mode == "w" then
		return {
			write = function(_, content)
				capturedSwitcherFeeds[#capturedSwitcherFeeds + 1] = content
			end,
			close = function() end,
		}
	end
	return realIoOpen(path, mode)
end

local fixtureCurrentWorkspaceWindowList = {
	focused = 2,
	windows = {
		{ ["window-id"] = 1, ["app-name"] = "Google Chrome", ["window-title"] = "ambient-canvas-gpu-screensaver" },
		{ ["window-id"] = 2, ["app-name"] = "WezTerm", ["window-title"] = "shell" },
	},
}

package.loaded["workspace_grid"] = {
	currentWorkspaceWindowList = function()
		return fixtureCurrentWorkspaceWindowList
	end,
	focusWindowById = function() end,
}

hs = {
	json = {
		encode = function(value)
			return value
		end,
	},
	timer = {
		doEvery = function()
			return { start = function() end }
		end,
	},
	pathwatcher = {
		new = function()
			return { start = function() end }
		end,
	},
}

require("switcher_bridge")

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

local switcherFeed = capturedSwitcherFeeds[1]
expectEqual("the switcher feed is written once on load", 1, #capturedSwitcherFeeds)
expectEqual("the pinned screensaver is dropped, leaving only the ordinary window", 1, #switcherFeed.windows)
expectEqual("the surviving switcher entry is the ordinary window", 2, switcherFeed.windows[1]["window-id"])
expectEqual("the focused id is preserved verbatim for the daemon", 2, switcherFeed.focused)

os.exit(failureCount == 0 and 0 or 1)
