local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local createdMenuBarItems = {}
hs = {
	menubar = {
		new = function()
			local menuBarItem = { deleted = false, title = nil, menuItemBuilder = nil }
			function menuBarItem:setTitle(newTitle)
				self.title = newTitle
			end
			function menuBarItem:setMenu(buildMenuItems)
				self.menuItemBuilder = buildMenuItems
			end
			function menuBarItem:delete()
				self.deleted = true
			end
			table.insert(createdMenuBarItems, menuBarItem)
			return menuBarItem
		end,
	},
	styledtext = {
		new = function(text, attributes)
			return {
				text = text,
				font = attributes and attributes.font or nil,
				color = attributes and attributes.color or nil,
			}
		end,
	},
}

local menuBarItem = require("workspace_grid_window_menu_bar_item")

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

expectEqual("loading the module claims exactly one slot in the menu bar", 1, #createdMenuBarItems)

local builtMenuItems = { { title = "a window" } }
menuBarItem.installMenuItemBuilder(function()
	return builtMenuItems
end)

local installedItem = createdMenuBarItems[1]
expectEqual("the item carries a visible glyph so it can be found and clicked", "⌘⇥", installedItem.title.text)
expectEqual("the glyph follows the bar's own label color", "labelColor", installedItem.title.color.name)
expectEqual(
	"the glyph is drawn in the same monospaced font as the workspace indicator",
	"Menlo",
	installedItem.title.font.name
)
expectEqual("the item opens the menu the builder returns", builtMenuItems, installedItem.menuItemBuilder())

menuBarItem.deleteMenuBarItem()
expectEqual("a reload removes the item instead of orphaning it in the bar", true, installedItem.deleted)

menuBarItem.deleteMenuBarItem()
menuBarItem.installMenuItemBuilder(function()
	return {}
end)
expectEqual("installing after a delete claims no second slot", 1, #createdMenuBarItems)

os.exit(failureCount == 0 and 0 or 1)
