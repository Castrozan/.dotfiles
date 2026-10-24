local M = {}

local function origin_host()
  local origin = vim.trim(vim.fn.system({ "git", "remote", "get-url", "origin" }))
  if vim.v.shell_error ~= 0 then
    return nil
  end
  return origin:gsub("^%a[%w+.-]*://", ""):gsub("^[^@/]*@", ""):match("^([^/:]+)")
end

function M.provide()
  local host = origin_host()
  if not host then
    return nil, nil, "no origin remote to find the GitLab host"
  end
  local token = vim.trim(vim.fn.system({ "glab", "config", "get", "token", "--host", host }))
  if vim.v.shell_error ~= 0 or token == "" then
    return nil, nil, "glab has no token for " .. host .. ": run glab auth login"
  end
  return token, "https://" .. host, nil
end

return M
