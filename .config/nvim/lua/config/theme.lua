local dynamic_theme = {}

local wallpaper_palette_file_path = vim.fn.expand("~/.config/hypr-theme/current/theme/colors.toml")
local theme_change_signal_file_path = vim.fn.expand("~/.config/hypr-theme/current/theme.name")

local fallback_palette_when_no_dynamic_theme_present = {
  background = "#05070e",
  foreground = "#fbfbf8",
  color0 = "#05070e",
  color1 = "#b05828",
  color2 = "#60d13b",
  color3 = "#e9d13e",
  color4 = "#1537a8",
  color5 = "#7a5cc0",
  color6 = "#2cb7d0",
  color7 = "#fbfbf8",
  color8 = "#505156",
  color9 = "#e46017",
  color10 = "#6eeb44",
  color11 = "#f5df55",
  color12 = "#0c3bd4",
  color13 = "#9b7fe0",
  color14 = "#34cfeb",
  color15 = "#fdfdfb",
}

local function read_wallpaper_palette_from_disk()
  local palette_file = io.open(wallpaper_palette_file_path, "r")
  if not palette_file then
    return vim.deepcopy(fallback_palette_when_no_dynamic_theme_present)
  end
  local palette = {}
  for line in palette_file:lines() do
    local color_name, hex_value = line:match('^%s*([%w_]+)%s*=%s*"(#%x+)"')
    if color_name and hex_value then
      palette[color_name] = hex_value
    end
  end
  palette_file:close()
  for color_name, hex_value in pairs(fallback_palette_when_no_dynamic_theme_present) do
    if not palette[color_name] then
      palette[color_name] = hex_value
    end
  end
  return palette
end

local function blend_two_hex_colors(first_hex, second_hex, second_color_weight)
  local function red_green_blue_channels(hex)
    return tonumber(hex:sub(2, 3), 16), tonumber(hex:sub(4, 5), 16), tonumber(hex:sub(6, 7), 16)
  end
  local first_red, first_green, first_blue = red_green_blue_channels(first_hex)
  local second_red, second_green, second_blue = red_green_blue_channels(second_hex)
  local function mixed_channel(first_channel, second_channel)
    return math.floor(first_channel + (second_channel - first_channel) * second_color_weight + 0.5)
  end
  return string.format(
    "#%02x%02x%02x",
    mixed_channel(first_red, second_red),
    mixed_channel(first_green, second_green),
    mixed_channel(first_blue, second_blue)
  )
end

local function map_wallpaper_palette_to_base16(palette)
  local background = palette.background
  local foreground = palette.foreground
  return {
    base00 = background,
    base01 = blend_two_hex_colors(background, foreground, 0.06),
    base02 = blend_two_hex_colors(background, foreground, 0.13),
    base03 = palette.color8,
    base04 = blend_two_hex_colors(palette.color8, foreground, 0.5),
    base05 = foreground,
    base06 = blend_two_hex_colors(foreground, palette.color15, 0.5),
    base07 = palette.color15,
    base08 = palette.color1,
    base09 = palette.color9,
    base0A = palette.color3,
    base0B = palette.color2,
    base0C = palette.color6,
    base0D = palette.color4,
    base0E = palette.color5,
    base0F = palette.color9,
  }
end

local highlight_groups_to_make_transparent = {
  "Normal",
  "NormalNC",
  "NormalFloat",
  "FloatBorder",
  "FloatTitle",
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
  "WhichKey",
  "WhichKeyFloat",
  "WhichKeyBorder",
  "TelescopeNormal",
  "TelescopeBorder",
  "TelescopePromptNormal",
  "TelescopePromptBorder",
  "TelescopeResultsNormal",
  "TelescopePreviewNormal",
  "NotifyBackground",
  "SnacksNormal",
  "SnacksNormalNC",
  "SnacksWinBar",
  "SnacksWinBarNC",
  "SnacksPicker",
  "SnacksPickerList",
  "SnacksPickerInput",
  "SnacksPickerPreview",
  "SnacksPickerBox",
  "SnacksDashboardNormal",
}

local function clear_backgrounds_to_let_terminal_show_through()
  for _, group_name in ipairs(highlight_groups_to_make_transparent) do
    local resolved_highlight = vim.api.nvim_get_hl(0, { name = group_name, link = false })
    resolved_highlight.bg = nil
    resolved_highlight.ctermbg = nil
    vim.api.nvim_set_hl(0, group_name, resolved_highlight)
  end
end

function dynamic_theme.apply()
  local base16_palette = map_wallpaper_palette_to_base16(read_wallpaper_palette_from_disk())
  local base16_module_is_available, base16_module = pcall(require, "base16-colorscheme")
  if not base16_module_is_available then
    return
  end
  base16_module.setup(base16_palette)
  clear_backgrounds_to_let_terminal_show_through()
end

local wallpaper_theme_change_watcher

local function arm_wallpaper_theme_change_watcher()
  if not wallpaper_theme_change_watcher then
    return
  end
  pcall(function()
    wallpaper_theme_change_watcher:start(
      theme_change_signal_file_path,
      {},
      vim.schedule_wrap(function()
        dynamic_theme.apply()
        wallpaper_theme_change_watcher:stop()
        arm_wallpaper_theme_change_watcher()
      end)
    )
  end)
end

function dynamic_theme.setup_live_reload_on_wallpaper_change()
  if not wallpaper_theme_change_watcher then
    wallpaper_theme_change_watcher = vim.uv.new_fs_event()
    arm_wallpaper_theme_change_watcher()
  end

  vim.api.nvim_create_autocmd("FocusGained", {
    group = vim.api.nvim_create_augroup("ReapplyDynamicThemeOnFocusGained", { clear = true }),
    callback = function()
      dynamic_theme.apply()
    end,
  })

  vim.api.nvim_create_user_command("ThemeReload", function()
    dynamic_theme.apply()
  end, { desc = "Re-read the wallpaper palette and re-apply the dynamic theme" })
end

return dynamic_theme
