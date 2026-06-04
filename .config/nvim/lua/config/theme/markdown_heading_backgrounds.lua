local markdown_heading_backgrounds = {}

local heading_color_weight_over_background = 0.1
local highest_heading_level = 6

local function red_green_blue_from_hex(hex)
  return tonumber(hex:sub(2, 3), 16), tonumber(hex:sub(4, 5), 16), tonumber(hex:sub(6, 7), 16)
end

local function hex_from_decimal_color(decimal_color)
  return string.format("#%06x", decimal_color)
end

local function blend_foreground_over_background(foreground_hex, background_hex, foreground_weight)
  local foreground_red, foreground_green, foreground_blue = red_green_blue_from_hex(foreground_hex)
  local background_red, background_green, background_blue = red_green_blue_from_hex(background_hex)
  local function mixed_channel(foreground_channel, background_channel)
    return math.floor(background_channel + (foreground_channel - background_channel) * foreground_weight + 0.5)
  end
  return string.format(
    "#%02x%02x%02x",
    mixed_channel(foreground_red, background_red),
    mixed_channel(foreground_green, background_green),
    mixed_channel(foreground_blue, background_blue)
  )
end

function markdown_heading_backgrounds.soften_against_background(background_hex)
  for heading_level = 1, highest_heading_level do
    local heading_foreground_group = "RenderMarkdownH" .. heading_level
    local heading_background_group = heading_foreground_group .. "Bg"
    local heading_highlight = vim.api.nvim_get_hl(0, { name = heading_foreground_group, link = false })
    if heading_highlight.fg then
      vim.api.nvim_set_hl(0, heading_background_group, {
        bg = blend_foreground_over_background(
          hex_from_decimal_color(heading_highlight.fg),
          background_hex,
          heading_color_weight_over_background
        ),
      })
    end
  end
end

return markdown_heading_backgrounds
