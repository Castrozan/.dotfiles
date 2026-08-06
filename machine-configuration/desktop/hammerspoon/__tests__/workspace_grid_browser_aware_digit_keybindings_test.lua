local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local workspaceColumnByKeyCode = {
	[18] = 1,
	[19] = 2,
	[20] = 3,
	[21] = 4,
	[22] = 5,
	[23] = 6,
	[24] = 7,
}

local frontmostBundleIdentifier = nil
local switchedWorkspaceNumbers = {}
local createdEventTaps = {}

hs = {
	application = {
		frontmostApplication = function()
			if frontmostBundleIdentifier == nil then
				return nil
			end
			return {
				bundleID = function()
					return frontmostBundleIdentifier
				end,
			}
		end,
	},
	eventtap = {
		event = {
			types = { keyDown = { name = "keyDown" } },
		},
		new = function(_, eventHandler)
			local eventTap = {
				eventHandler = eventHandler,
				started = false,
			}
			function eventTap:start()
				self.started = true
			end
			table.insert(createdEventTaps, eventTap)
			return eventTap
		end,
	},
}

local digitKeybindings = require("workspace_grid_browser_aware_digit_keybindings")

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

local function routingDecisionFor(eventFlags, keyCode, bundleIdentifier)
	return digitKeybindings.buildRoutingDecision(eventFlags, keyCode, bundleIdentifier, workspaceColumnByKeyCode)
end

expectEqual("plain Cmd+1 outside a browser switches to workspace one", 1, routingDecisionFor({ cmd = true }, 18, nil))
expectEqual(
	"plain Cmd+7 outside a browser switches to workspace seven",
	7,
	routingDecisionFor({ cmd = true }, 24, "com.apple.Terminal")
)
expectEqual(
	"plain Cmd+1 with Chrome frontmost passes through to the browser",
	nil,
	routingDecisionFor({ cmd = true }, 18, "com.google.Chrome")
)
expectEqual(
	"plain Cmd+1 with Brave frontmost passes through to the browser",
	nil,
	routingDecisionFor({ cmd = true }, 18, "com.brave.Browser")
)
expectEqual(
	"Cmd+Alt+1 is not routed by this binding because row two stays a plain hotkey",
	nil,
	routingDecisionFor({ cmd = true, alt = true }, 18, "com.google.Chrome")
)
expectEqual(
	"Cmd+Ctrl+1 is not routed by this binding because row three stays a plain hotkey",
	nil,
	routingDecisionFor({ cmd = true, ctrl = true }, 18, "com.google.Chrome")
)
expectEqual(
	"Cmd+Shift+1 is not routed by this binding because window moves stay a plain hotkey",
	nil,
	routingDecisionFor({ cmd = true, shift = true }, 18, "com.google.Chrome")
)
expectEqual("plain Cmd+8 is not a bound workspace column", nil, routingDecisionFor({ cmd = true }, 25, nil))
expectEqual("plain Cmd with a letter key is not a workspace column", nil, routingDecisionFor({ cmd = true }, 0, nil))

local fakeWorkspaceGrid = {
	switchToWorkspace = function(workspaceNumber)
		table.insert(switchedWorkspaceNumbers, workspaceNumber)
	end,
}

frontmostBundleIdentifier = "com.google.Chrome"
digitKeybindings.install({ workspaceGrid = fakeWorkspaceGrid, workspaceColumnByKeyCode = workspaceColumnByKeyCode })
expectEqual("install registers exactly one keydown event tap", 1, #createdEventTaps)
expectEqual("the keydown event tap starts immediately", true, createdEventTaps[1].started)

local chromePassThroughResult = createdEventTaps[1].eventHandler({
	getFlags = function()
		return { cmd = true }
	end,
	getKeyCode = function()
		return 18
	end,
})
expectEqual("a Cmd+1 keydown with Chrome frontmost passes through untouched", nil, chromePassThroughResult)
expectEqual("a browser pass-through never switches workspace", 0, #switchedWorkspaceNumbers)

frontmostBundleIdentifier = "com.apple.Terminal"
local terminalSwitchResult = createdEventTaps[1].eventHandler({
	getFlags = function()
		return { cmd = true }
	end,
	getKeyCode = function()
		return 18
	end,
})
expectEqual("a Cmd+1 keydown with a terminal frontmost is consumed", true, terminalSwitchResult)
expectEqual("a consumed Cmd+1 switches to workspace one", 1, switchedWorkspaceNumbers[1])

os.exit(failureCount == 0 and 0 or 1)
