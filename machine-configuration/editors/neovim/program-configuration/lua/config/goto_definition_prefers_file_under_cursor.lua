local goto_definition_fallbacks_by_buffer = {}

local function readable_file_at(candidate_path)
  if vim.fn.filereadable(candidate_path) == 1 then
    return candidate_path
  end
  if vim.fn.isdirectory(candidate_path) == 1 then
    local directory_entry_point = candidate_path .. "/default.nix"
    if vim.fn.filereadable(directory_entry_point) == 1 then
      return directory_entry_point
    end
  end
  return nil
end

local function file_path_under_cursor()
  local path_under_cursor = vim.fn.expand("<cfile>")
  if path_under_cursor == "" or path_under_cursor:match("^%a[%w+.-]*://") then
    return nil
  end
  local current_file_directory = vim.fn.expand("%:p:h")
  for _, candidate_path in ipairs({ current_file_directory .. "/" .. path_under_cursor, path_under_cursor }) do
    local resolved_path = readable_file_at(vim.fs.normalize(vim.fn.fnamemodify(candidate_path, ":p")))
    if resolved_path then
      return resolved_path
    end
  end
  return nil
end

local function jump_to_file_under_cursor_or(fallback)
  local resolved_path = file_path_under_cursor()
  if resolved_path == nil then
    fallback()
    return false
  end
  vim.cmd.edit(vim.fn.fnameescape(resolved_path))
  return true
end

local function goto_definition_fallback_for(buffer_number)
  if goto_definition_fallbacks_by_buffer[buffer_number] then
    return goto_definition_fallbacks_by_buffer[buffer_number]
  end
  for _, mapping in ipairs(vim.api.nvim_buf_get_keymap(buffer_number, "n")) do
    if mapping.lhs == "gd" then
      if mapping.callback then
        return mapping.callback
      end
      local right_hand_side_keys = vim.api.nvim_replace_termcodes(mapping.rhs, true, false, true)
      return function()
        vim.api.nvim_feedkeys(right_hand_side_keys, "n", false)
      end
    end
  end
  return vim.lsp.buf.definition
end

local function install_for_buffer(buffer_number)
  if not vim.api.nvim_buf_is_valid(buffer_number) then
    return
  end
  local fallback = goto_definition_fallback_for(buffer_number)
  goto_definition_fallbacks_by_buffer[buffer_number] = fallback
  vim.keymap.set("n", "gd", function()
    jump_to_file_under_cursor_or(fallback)
  end, { buffer = buffer_number, desc = "Goto Definition or file under cursor" })
end

return {
  file_path_under_cursor = file_path_under_cursor,
  jump_to_file_under_cursor_or = jump_to_file_under_cursor_or,
  install = function()
    vim.api.nvim_create_autocmd("LspAttach", {
      callback = function(event)
        vim.schedule(function()
          install_for_buffer(event.buf)
        end)
      end,
    })
    vim.api.nvim_create_autocmd({ "BufDelete", "BufWipeout" }, {
      callback = function(event)
        goto_definition_fallbacks_by_buffer[event.buf] = nil
      end,
    })
  end,
}
