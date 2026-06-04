local map = vim.keymap.set

local file_explorer_width_state_file_path = vim.fn.stdpath("state") .. "/snacks-explorer-width.txt"
local default_file_explorer_width = 40

local function read_persisted_file_explorer_width()
  local file_handle = io.open(file_explorer_width_state_file_path, "r")
  if not file_handle then
    return default_file_explorer_width
  end
  local raw_value = file_handle:read("*l")
  file_handle:close()
  return tonumber(raw_value) or default_file_explorer_width
end

local function persist_file_explorer_width(new_width)
  local file_handle = io.open(file_explorer_width_state_file_path, "w")
  if not file_handle then
    return
  end
  file_handle:write(tostring(new_width))
  file_handle:close()
end

local function find_file_explorer_window_id()
  for _, window_id in ipairs(vim.api.nvim_list_wins()) do
    local buffer_id = vim.api.nvim_win_get_buf(window_id)
    if vim.api.nvim_get_option_value("filetype", { buf = buffer_id }) == "snacks_picker_list" then
      return window_id
    end
  end
  return nil
end

local function open_file_explorer_with_persisted_width()
  Snacks.explorer({
    hidden = true,
    follow = true,
    layout = { layout = { width = read_persisted_file_explorer_width() } },
  })
end

local function find_open_file_explorer_picker()
  local open_explorer_pickers = Snacks.picker.get({ source = "explorer" })
  return open_explorer_pickers[1]
end

local function show_or_hide_file_explorer()
  local open_explorer_picker = find_open_file_explorer_picker()
  if open_explorer_picker then
    open_explorer_picker:close()
  else
    open_file_explorer_with_persisted_width()
  end
end

map("n", "<C-S-b>", show_or_hide_file_explorer, { desc = "Show or hide file explorer" })

local function resize_file_explorer_width_by(width_delta)
  local explorer_window_id = find_file_explorer_window_id()
  if not explorer_window_id then
    vim.notify("file explorer is not open", vim.log.levels.WARN)
    return
  end
  local new_width = vim.api.nvim_win_get_width(explorer_window_id) + width_delta
  vim.api.nvim_win_set_width(explorer_window_id, new_width)
  persist_file_explorer_width(new_width)
end

map("n", "<C-S-k>", function()
  resize_file_explorer_width_by(5)
end, { desc = "Increase file explorer width" })
map("n", "<C-S-j>", function()
  resize_file_explorer_width_by(-5)
end, { desc = "Decrease file explorer width" })

map("n", "<C-S-e>", function()
  local current_filetype = vim.bo.filetype
  if current_filetype == "snacks_picker_list" or current_filetype == "snacks_picker_input" then
    vim.cmd("wincmd p")
    return
  end
  local open_explorer_picker = find_open_file_explorer_picker()
  if open_explorer_picker then
    open_explorer_picker:focus()
  else
    open_file_explorer_with_persisted_width()
  end
end, { desc = "Toggle file explorer focus" })

vim.api.nvim_create_autocmd("VimLeavePre", {
  group = vim.api.nvim_create_augroup("PersistFileExplorerWidthOnExit", { clear = true }),
  callback = function()
    local explorer_window_id = find_file_explorer_window_id()
    if explorer_window_id then
      persist_file_explorer_width(vim.api.nvim_win_get_width(explorer_window_id))
    end
  end,
})

local function move_focus_away_from_file_explorer_or_close_nvim()
  local current_window_id = vim.api.nvim_get_current_win()
  local other_non_floating_windows = vim.tbl_filter(function(window_id)
    if window_id == current_window_id then
      return false
    end
    return vim.api.nvim_win_get_config(window_id).relative == ""
  end, vim.api.nvim_list_wins())
  if #other_non_floating_windows == 0 then
    vim.cmd("qa")
  else
    vim.cmd("wincmd p")
  end
end

vim.api.nvim_create_autocmd("FileType", {
  group = vim.api.nvim_create_augroup("RedirectQuitFromFileExplorer", { clear = true }),
  pattern = "snacks_picker_list",
  callback = function(file_type_event)
    vim.api.nvim_buf_create_user_command(
      file_type_event.buf,
      "QuitFileExplorerOrCloseNvim",
      move_focus_away_from_file_explorer_or_close_nvim,
      {}
    )
    vim.cmd("cnoreabbrev <buffer> q QuitFileExplorerOrCloseNvim")
    vim.cmd("cnoreabbrev <buffer> quit QuitFileExplorerOrCloseNvim")
  end,
})
