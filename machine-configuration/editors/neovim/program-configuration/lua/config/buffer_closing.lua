local function find_other_listed_file_buffer_than(excluded_buffer_id)
  for _, buffer_id in ipairs(vim.api.nvim_list_bufs()) do
    if
      buffer_id ~= excluded_buffer_id
      and vim.api.nvim_buf_is_valid(buffer_id)
      and vim.bo[buffer_id].buflisted
      and vim.api.nvim_buf_get_name(buffer_id) ~= ""
    then
      return buffer_id
    end
  end
  return nil
end

local function current_buffer_represents_a_file()
  return vim.bo.buflisted and vim.api.nvim_buf_get_name(0) ~= ""
end

local function listed_file_buffer_ids_in_visual_order()
  local bufferline_is_available, bufferline = pcall(require, "bufferline")
  if bufferline_is_available and bufferline.get_elements then
    local ordered_buffer_ids = {}
    for _, element in ipairs(bufferline.get_elements().elements) do
      table.insert(ordered_buffer_ids, element.id)
    end
    if #ordered_buffer_ids > 0 then
      return ordered_buffer_ids
    end
  end
  local ordered_buffer_ids = {}
  for _, buffer_id in ipairs(vim.api.nvim_list_bufs()) do
    if
      vim.api.nvim_buf_is_valid(buffer_id)
      and vim.bo[buffer_id].buflisted
      and vim.api.nvim_buf_get_name(buffer_id) ~= ""
    then
      table.insert(ordered_buffer_ids, buffer_id)
    end
  end
  return ordered_buffer_ids
end

local function find_buffer_to_focus_after_closing(buffer_to_close)
  local ordered_buffer_ids = listed_file_buffer_ids_in_visual_order()
  for index, buffer_id in ipairs(ordered_buffer_ids) do
    if buffer_id == buffer_to_close then
      return ordered_buffer_ids[index + 1] or ordered_buffer_ids[index - 1]
    end
  end
  return ordered_buffer_ids[#ordered_buffer_ids]
end

local function close_current_buffer_focusing_right_then_left()
  if not current_buffer_represents_a_file() then
    return
  end
  local buffer_to_close = vim.api.nvim_get_current_buf()
  if not find_other_listed_file_buffer_than(buffer_to_close) then
    Snacks.dashboard({ win = vim.api.nvim_get_current_win() })
    vim.cmd("bdelete " .. buffer_to_close)
    return
  end
  local buffer_to_focus = find_buffer_to_focus_after_closing(buffer_to_close)
  if buffer_to_focus and buffer_to_focus ~= buffer_to_close then
    vim.api.nvim_set_current_buf(buffer_to_focus)
  end
  vim.cmd("bdelete " .. buffer_to_close)
end

return {
  close_current_buffer_focusing_right_then_left = close_current_buffer_focusing_right_then_left,
  listed_file_buffer_ids_in_visual_order = listed_file_buffer_ids_in_visual_order,
  find_buffer_to_focus_after_closing = find_buffer_to_focus_after_closing,
}
