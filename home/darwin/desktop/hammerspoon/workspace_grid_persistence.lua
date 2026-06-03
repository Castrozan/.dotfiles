local workspaceGridPersistence = {}

local stateFilePathOverrideForTest = nil

local function resolveStateFilePath()
  return stateFilePathOverrideForTest
    or os.getenv("HAMMERSPOON_WORKSPACE_STATE_FILE")
    or (os.getenv("HOME") .. "/.cache/hammerspoon/workspace-grid-state")
end

function workspaceGridPersistence.setStateFilePathForTest(stateFilePath)
  stateFilePathOverrideForTest = stateFilePath
end

local function ensureParentDirectoryExists(filePath)
  local parentDirectory = filePath:match("^(.*)/[^/]+$")
  if parentDirectory then
    os.execute("mkdir -p '" .. parentDirectory .. "'")
  end
end

function workspaceGridPersistence.save(currentWorkspaceNumber, workspaceNumberByWindowId)
  local stateFilePath = resolveStateFilePath()
  ensureParentDirectoryExists(stateFilePath)
  local file = io.open(stateFilePath, "w")
  if not file then
    return
  end
  file:write(tostring(currentWorkspaceNumber) .. "\n")
  for windowId, workspaceNumber in pairs(workspaceNumberByWindowId) do
    file:write(tostring(windowId) .. " " .. tostring(workspaceNumber) .. "\n")
  end
  file:close()
end

function workspaceGridPersistence.load()
  local workspaceNumberByWindowId = {}
  local file = io.open(resolveStateFilePath(), "r")
  if not file then
    return nil, workspaceNumberByWindowId
  end
  local currentWorkspaceNumber = tonumber(file:read("l"))
  for line in file:lines() do
    local windowId, workspaceNumber = line:match("^(%-?%d+)%s+(%d+)$")
    if windowId then
      workspaceNumberByWindowId[tonumber(windowId)] = tonumber(workspaceNumber)
    end
  end
  file:close()
  return currentWorkspaceNumber, workspaceNumberByWindowId
end

return workspaceGridPersistence
