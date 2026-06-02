local fill_section_names_to_make_transparent = { "b", "c", "x" }

local function derive_lualine_theme_with_transparent_fill()
  local auto_theme = require("lualine.themes.auto")
  for _, mode_highlight_groups in pairs(auto_theme) do
    for _, fill_section_name in ipairs(fill_section_names_to_make_transparent) do
      local section_highlight = mode_highlight_groups[fill_section_name]
      if section_highlight then
        section_highlight.bg = "NONE"
      end
    end
  end
  return auto_theme
end

return {
  "nvim-lualine/lualine.nvim",
  opts = function(_, opts)
    opts.options = opts.options or {}
    opts.options.theme = derive_lualine_theme_with_transparent_fill()
  end,
}
