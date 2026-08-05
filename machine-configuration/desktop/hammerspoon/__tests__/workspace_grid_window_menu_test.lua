local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

hs = {
	image = {
		imageFromAppBundle = function(bundleIdentifier)
			local fakeIcon = { bundleIdentifier = bundleIdentifier }
			function fakeIcon:setSize()
				return self
			end
			return fakeIcon
		end,
	},
}

local windowMenu = require("workspace_grid_window_menu")

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

local function windowDescriptor(windowId, applicationName, windowTitle)
	return {
		["window-id"] = windowId,
		["app-name"] = applicationName,
		["app-bundle-id"] = "com.example." .. applicationName:lower(),
		["window-title"] = windowTitle,
	}
end

local revealedWindowIds = {}
local function recordRevealedWindowId(windowId)
	table.insert(revealedWindowIds, windowId)
end

local populatedSnapshot = {
	descriptorsByWorkspaceNumber = {
		[18] = { windowDescriptor(3, "WezTerm", "bash"), windowDescriptor(1, "Chrome", "YouTube") },
		[4] = { windowDescriptor(7, "Slack", "general") },
		[11] = { windowDescriptor(9, "Notes", "todo") },
	},
	focusedWindowId = 3,
}

local menuItems = windowMenu.menuItemsForSnapshot(populatedSnapshot, 18, recordRevealedWindowId)

expectEqual("every workspace heading, window and separator is rendered", 9, #menuItems)
expectEqual(
	"the current workspace heads the menu even when its number is not the lowest",
	"Workspace 18 (current)",
	menuItems[1].title
)
expectEqual("a heading is not clickable", true, menuItems[1].disabled)
expectEqual("windows sort by application so a mouse target keeps its position", "YouTube", menuItems[2].title)
expectEqual("the second window of the current workspace follows its application order", "bash", menuItems[3].title)
expectEqual("the focused window is checked", true, menuItems[3].checked)
expectEqual("an unfocused window is not checked", false, menuItems[2].checked)
expectEqual("window rows are indented under their heading", 1, menuItems[2].indent)
expectEqual("a window row carries its application icon", "com.example.chrome", menuItems[2].image.bundleIdentifier)
expectEqual("a separator divides two workspace sections", "-", menuItems[4].title)
expectEqual("the remaining workspaces follow in ascending order", "Workspace 4", menuItems[5].title)
expectEqual("a workspace that is not current carries no current marker", "Workspace 11", menuItems[8].title)

menuItems[6].fn()
expectEqual("clicking a window row reveals exactly that window", 1, #revealedWindowIds)
expectEqual("clicking a window row reveals it by its own id", 7, revealedWindowIds[1])

local emptyGridMenuItems =
	windowMenu.menuItemsForSnapshot({ descriptorsByWorkspaceNumber = {} }, 11, recordRevealedWindowId)
expectEqual("an empty grid renders a single row", 1, #emptyGridMenuItems)
expectEqual("an empty grid says so", "No windows", emptyGridMenuItems[1].title)
expectEqual("the empty-grid row is not clickable", true, emptyGridMenuItems[1].disabled)

local longMultiByteTitle = string.rep("ç", 90)
local truncatedMenuItems = windowMenu.menuItemsForSnapshot({
	descriptorsByWorkspaceNumber = { [1] = { windowDescriptor(2, "Chrome", longMultiByteTitle) } },
}, 1, recordRevealedWindowId)
expectEqual(
	"a long title is cut to the cap plus an ellipsis without splitting a multi-byte character",
	61,
	utf8.len(truncatedMenuItems[2].title)
)

local untitledWindowMenuItems = windowMenu.menuItemsForSnapshot({
	descriptorsByWorkspaceNumber = { [1] = { windowDescriptor(2, "Chrome", "") } },
}, 1, recordRevealedWindowId)
expectEqual("a window with no title falls back to its application name", "Chrome", untitledWindowMenuItems[2].title)

os.exit(failureCount == 0 and 0 or 1)
