local M = {}

local LOAD_POLL_MILLISECONDS = 100
local LOAD_TIMEOUT_MILLISECONDS = 30000

local function start_review_once_loaded(buffer_number, remaining_milliseconds)
  local pull_request_buffer = _G.octo_buffers and _G.octo_buffers[buffer_number]
  if pull_request_buffer and pull_request_buffer:isPullRequest() then
    require("octo.reviews").start_or_resume_review()
    return
  end
  if remaining_milliseconds <= 0 then
    vim.notify("The pull request did not load in time", vim.log.levels.ERROR)
    return
  end
  vim.defer_fn(function()
    start_review_once_loaded(buffer_number, remaining_milliseconds - LOAD_POLL_MILLISECONDS)
  end, LOAD_POLL_MILLISECONDS)
end

function M.open(pull_request_url)
  local octo_path = pull_request_url:gsub("^https?://github%.com/", ""):gsub("^https?://", "")
  vim.cmd.edit("octo://" .. octo_path)
  start_review_once_loaded(vim.api.nvim_get_current_buf(), LOAD_TIMEOUT_MILLISECONDS)
end

return M
