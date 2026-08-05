local transparency = {}

local page_and_chrome_groups_to_make_fully_transparent = {
  "Normal",
  "NormalNC",
  "SignColumn",
  "LineNr",
  "CursorLineNr",
  "FoldColumn",
  "EndOfBuffer",
  "MsgArea",
  "MsgSeparator",
  "TablineFill",
  "StatusLine",
  "StatusLineNC",
  "WinBar",
  "WinBarNC",
  "SnacksNormal",
  "SnacksNormalNC",
  "SnacksPickerBox",
  "SnacksPickerList",
  "SnacksPickerInput",
  "SnacksPickerBoxBorder",
  "SnacksPickerListBorder",
  "SnacksPickerInputBorder",
}

local function strip_background_from_highlight_group(group_name)
  local resolved_highlight = vim.api.nvim_get_hl(0, { name = group_name, link = false })
  if vim.tbl_isempty(resolved_highlight) then
    return
  end
  resolved_highlight.bg = nil
  resolved_highlight.ctermbg = nil
  vim.api.nvim_set_hl(0, group_name, resolved_highlight)
end

function transparency.clear_backgrounds_to_let_terminal_show_through()
  for _, group_name in ipairs(page_and_chrome_groups_to_make_fully_transparent) do
    strip_background_from_highlight_group(group_name)
  end
end

return transparency
