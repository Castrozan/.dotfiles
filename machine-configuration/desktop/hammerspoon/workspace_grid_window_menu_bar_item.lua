local workspaceGridWindowMenuBarItem = {}

local menuBarItemGlyph = "⌘⇥"
local menuBarItemFont = { name = "Menlo", size = 13 }
local menuBarItemColor = { list = "System", name = "labelColor" }

local menuBarItemHandle = hs.menubar.new()

function workspaceGridWindowMenuBarItem.installMenuItemBuilder(buildMenuItems)
	if not menuBarItemHandle then
		return
	end
	menuBarItemHandle:setTitle(
		hs.styledtext.new(menuBarItemGlyph, { font = menuBarItemFont, color = menuBarItemColor })
	)
	menuBarItemHandle:setMenu(buildMenuItems)
end

function workspaceGridWindowMenuBarItem.deleteMenuBarItem()
	if menuBarItemHandle then
		menuBarItemHandle:delete()
		menuBarItemHandle = nil
	end
end

return workspaceGridWindowMenuBarItem
