local file_explorer = {}

local function find_open_file_explorer_picker()
  return Snacks.picker.get({ source = "explorer" })[1]
end

local function is_cursor_inside_file_explorer_window()
  local current_filetype = vim.bo.filetype
  return current_filetype == "snacks_picker_list" or current_filetype == "snacks_picker_input"
end

local function return_focus_to_editor_window(open_explorer_picker)
  local main_window_id = open_explorer_picker and open_explorer_picker.main
  if main_window_id and vim.api.nvim_win_is_valid(main_window_id) then
    vim.api.nvim_set_current_win(main_window_id)
  else
    vim.cmd("wincmd p")
  end
end

function file_explorer.toggle_visibility()
  Snacks.explorer()
end

function file_explorer.toggle_focus()
  local open_explorer_picker = find_open_file_explorer_picker()
  if is_cursor_inside_file_explorer_window() then
    return_focus_to_editor_window(open_explorer_picker)
    return
  end
  if open_explorer_picker then
    open_explorer_picker:focus()
  else
    Snacks.explorer()
  end
end

return file_explorer
