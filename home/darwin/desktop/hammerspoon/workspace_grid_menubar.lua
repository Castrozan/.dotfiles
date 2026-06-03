-- Owns the menu-bar workspace indicator: renders "1 2 [3] 4 ..." with the
-- active workspace bracketed. Kept separate from the window-management grid so
-- each module has a single responsibility.

local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

function workspaceGridMenuBar.render(currentWorkspaceNumber, totalWorkspaceCount)
  if not menuBarIndicatorHandle then
    return
  end
  local segments = {}
  for workspaceNumber = 1, totalWorkspaceCount do
    if workspaceNumber == currentWorkspaceNumber then
      table.insert(segments, "[" .. workspaceNumber .. "]")
    else
      table.insert(segments, tostring(workspaceNumber))
    end
  end
  menuBarIndicatorHandle:setTitle(table.concat(segments, " "))
end

-- Called from hs.shutdownCallback before a reload so the old indicator is removed
-- instead of lingering as an orphan frozen at the workspace it last showed.
function workspaceGridMenuBar.deleteIndicator()
  if menuBarIndicatorHandle then
    menuBarIndicatorHandle:delete()
    menuBarIndicatorHandle = nil
  end
end

return workspaceGridMenuBar
