local accent_contrast_floor = {}

local minimum_accent_contrast_ratio_against_background = 4.5
local accent_lightness_step_while_lifting_for_contrast = 0.02
local accent_normal_slot_numbers = { 1, 2, 3, 4, 5, 6 }

local function red_green_blue_from_hex(hex)
  return tonumber(hex:sub(2, 3), 16), tonumber(hex:sub(4, 5), 16), tonumber(hex:sub(6, 7), 16)
end

local function hue_lightness_saturation_from_normalized_rgb(red, green, blue)
  local maximum = math.max(red, green, blue)
  local minimum = math.min(red, green, blue)
  local lightness = (maximum + minimum) / 2.0
  if maximum == minimum then
    return 0.0, lightness, 0.0
  end
  local range = maximum - minimum
  local saturation
  if lightness <= 0.5 then
    saturation = range / (maximum + minimum)
  else
    saturation = range / (2.0 - maximum - minimum)
  end
  local red_offset = (maximum - red) / range
  local green_offset = (maximum - green) / range
  local blue_offset = (maximum - blue) / range
  local hue
  if red == maximum then
    hue = blue_offset - green_offset
  elseif green == maximum then
    hue = 2.0 + red_offset - blue_offset
  else
    hue = 4.0 + green_offset - red_offset
  end
  return (hue / 6.0) % 1.0, lightness, saturation
end

local function single_normalized_channel_from_hue(lower_bound, upper_bound, hue)
  hue = hue % 1.0
  if hue < 1.0 / 6.0 then
    return lower_bound + (upper_bound - lower_bound) * hue * 6.0
  elseif hue < 0.5 then
    return upper_bound
  elseif hue < 2.0 / 3.0 then
    return lower_bound + (upper_bound - lower_bound) * (2.0 / 3.0 - hue) * 6.0
  end
  return lower_bound
end

local function normalized_rgb_from_hue_lightness_saturation(hue, lightness, saturation)
  if saturation == 0.0 then
    return lightness, lightness, lightness
  end
  local upper_bound
  if lightness <= 0.5 then
    upper_bound = lightness * (1.0 + saturation)
  else
    upper_bound = lightness + saturation - lightness * saturation
  end
  local lower_bound = 2.0 * lightness - upper_bound
  return single_normalized_channel_from_hue(lower_bound, upper_bound, hue + 1.0 / 3.0),
    single_normalized_channel_from_hue(lower_bound, upper_bound, hue),
    single_normalized_channel_from_hue(lower_bound, upper_bound, hue - 1.0 / 3.0)
end

local function linearized_srgb_channel(channel_value)
  local normalized = channel_value / 255.0
  if normalized <= 0.03928 then
    return normalized / 12.92
  end
  return ((normalized + 0.055) / 1.055) ^ 2.4
end

local function relative_luminance(red, green, blue)
  return 0.2126 * linearized_srgb_channel(red)
    + 0.7152 * linearized_srgb_channel(green)
    + 0.0722 * linearized_srgb_channel(blue)
end

local function contrast_ratio_between(first_red, first_green, first_blue, second_red, second_green, second_blue)
  local first_luminance = relative_luminance(first_red, first_green, first_blue)
  local second_luminance = relative_luminance(second_red, second_green, second_blue)
  local lighter = math.max(first_luminance, second_luminance)
  local darker = math.min(first_luminance, second_luminance)
  return (lighter + 0.05) / (darker + 0.05)
end

local function lighten_hex_until_minimum_contrast(color_hex, background_red, background_green, background_blue)
  local red, green, blue = red_green_blue_from_hex(color_hex)
  local hue, lightness, saturation =
    hue_lightness_saturation_from_normalized_rgb(red / 255.0, green / 255.0, blue / 255.0)
  while
    contrast_ratio_between(red, green, blue, background_red, background_green, background_blue)
      < minimum_accent_contrast_ratio_against_background
    and lightness < 1.0
  do
    lightness = math.min(1.0, lightness + accent_lightness_step_while_lifting_for_contrast)
    local normalized_red, normalized_green, normalized_blue =
      normalized_rgb_from_hue_lightness_saturation(hue, lightness, saturation)
    red = math.floor(normalized_red * 255)
    green = math.floor(normalized_green * 255)
    blue = math.floor(normalized_blue * 255)
  end
  return string.format("#%02x%02x%02x", red, green, blue)
end

local function yiq_luminance_of_hex(color_hex)
  local red, green, blue = red_green_blue_from_hex(color_hex)
  return (red * 299 + green * 587 + blue * 114) / 1000.0
end

function accent_contrast_floor.lift_accent_slots_against_background(palette)
  local background_red, background_green, background_blue = red_green_blue_from_hex(palette.background)
  for _, normal_slot_number in ipairs(accent_normal_slot_numbers) do
    local normal_slot_name = "color" .. normal_slot_number
    local bright_slot_name = "color" .. (normal_slot_number + 8)
    palette[normal_slot_name] =
      lighten_hex_until_minimum_contrast(palette[normal_slot_name], background_red, background_green, background_blue)
    palette[bright_slot_name] =
      lighten_hex_until_minimum_contrast(palette[bright_slot_name], background_red, background_green, background_blue)
    if yiq_luminance_of_hex(palette[bright_slot_name]) < yiq_luminance_of_hex(palette[normal_slot_name]) then
      palette[bright_slot_name] = palette[normal_slot_name]
    end
  end
  return palette
end

return accent_contrast_floor
