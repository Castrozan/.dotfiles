local markdown_highlights = {}

local function override_highlight_group(group_name, definition)
  vim.api.nvim_set_hl(0, group_name, definition)
end

function markdown_highlights.apply(base16_palette)
  local subtle_panel_background = base16_palette.base01
  local faint_structural_line = base16_palette.base03
  local inline_code_foreground = base16_palette.base0A

  for heading_level = 1, 6 do
    override_highlight_group("RenderMarkdownH" .. heading_level .. "Bg", {})
  end

  override_highlight_group("RenderMarkdownCode", { bg = subtle_panel_background })
  override_highlight_group("RenderMarkdownCodeInline", {
    fg = inline_code_foreground,
    bg = subtle_panel_background,
  })
  override_highlight_group("RenderMarkdownInlineHighlight", {
    fg = inline_code_foreground,
    bg = subtle_panel_background,
  })

  override_highlight_group("RenderMarkdownTableHead", { fg = base16_palette.base0C })
  override_highlight_group("RenderMarkdownTableRow", { fg = faint_structural_line })
  override_highlight_group("RenderMarkdownTableFill", {})

  override_highlight_group("RenderMarkdownDash", { fg = faint_structural_line })
  override_highlight_group("RenderMarkdownBullet", { fg = base16_palette.base0E })
  override_highlight_group("RenderMarkdownLink", { fg = base16_palette.base0C, underline = true })
  override_highlight_group("RenderMarkdownWikiLink", { fg = base16_palette.base0C, underline = true })
end

return markdown_highlights
