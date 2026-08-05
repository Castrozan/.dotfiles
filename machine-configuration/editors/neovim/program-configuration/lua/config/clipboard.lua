local M = {}

function M.paste_system_clipboard_as_single_line()
  local single_line_text = vim.fn.getreg("+"):gsub("[\r\n]+", " "):gsub("%s+$", "")
  if single_line_text == "" then
    return
  end
  vim.api.nvim_put({ single_line_text }, "c", false, true)
end

return M
