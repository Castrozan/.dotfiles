local transparency = {}

local highlight_groups_that_keep_their_background = {
  Visual = true,
  VisualNOS = true,
  Search = true,
  IncSearch = true,
  CurSearch = true,
  Substitute = true,
  DiffAdd = true,
  DiffChange = true,
  DiffDelete = true,
  DiffText = true,
}

local function strip_background(group_name, definition)
  if not definition.bg and not definition.ctermbg then
    return
  end
  definition.bg = nil
  definition.ctermbg = nil
  vim.api.nvim_set_hl(0, group_name, definition)
end

function transparency.clear_backgrounds_to_let_terminal_show_through()
  for group_name, definition in pairs(vim.api.nvim_get_hl(0, {})) do
    if not highlight_groups_that_keep_their_background[group_name] then
      strip_background(group_name, definition)
    end
  end
end

return transparency
