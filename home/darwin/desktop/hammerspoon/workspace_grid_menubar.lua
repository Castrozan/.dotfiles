-- Owns the menu-bar workspace indicator: renders only the active row's seven
-- workspaces, e.g. "15 16 17 [18] 19 20 21" on the third row, with the active
-- workspace bracketed. Kept separate from the window-management grid so each
-- module has a single responsibility.

local workspaceGridMenuBar = {}

local menuBarIndicatorHandle = hs.menubar.new()

function workspaceGridMenuBar.render(currentWorkspaceNumber, columnsPerRow)
  if not menuBarIndicatorHandle then
    return
  end
  local rowIndex = math.floor((currentWorkspaceNumber - 1) / columnsPerRow)
  local firstWorkspaceInRow = rowIndex * columnsPerRow + 1
  local lastWorkspaceInRow = firstWorkspaceInRow + columnsPerRow - 1
  local segments = {}
  for workspaceNumber = firstWorkspaceInRow, lastWorkspaceInRow do
    if workspaceNumber == currentWorkspaceNumber then
      table.insert(segments, "[" .. workspaceNumber .. "]")
    else
      table.insert(segments, tostring(workspaceNumber))
    end
  end
  menuBarIndicatorHandle:setTitle(table.concat(segments, " "))
end

function workspaceGridMenuBar.deleteIndicator()
  if menuBarIndicatorHandle then
    menuBarIndicatorHandle:delete()
    menuBarIndicatorHandle = nil
  end
end

return workspaceGridMenuBar
