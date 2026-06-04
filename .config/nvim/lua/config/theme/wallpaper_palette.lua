local accent_contrast_floor = require("config.theme.accent_contrast_floor")

local wallpaper_palette = {}

local wallpaper_palette_file_path = vim.fn.expand("~/.config/hypr-theme/current/theme/colors.toml")

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

function wallpaper_palette.read_and_map_to_base16()
  local palette = accent_contrast_floor.lift_accent_slots_against_background(read_wallpaper_palette_from_disk())
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

return wallpaper_palette
