-- WezTerm configuration
-- Ported from kitty config to match existing setup

local wezterm = require 'wezterm'

-- Catppuccin Mocha color scheme
local catppuccin_mocha = {
  -- Basic colors
  foreground = '#CDD6F4',
  background = '#1E1E2E',
  cursor_bg = '#F5E0DC',
  cursor_fg = '#1E1E2E',
  selection_bg = '#F5E0DC',
  selection_fg = '#1E1E2E',

  -- 16 terminal colors
  ansi = {
    '#45475A', -- black
    '#F38BA8', -- red
    '#A6E3A1', -- green
    '#F9E2AF', -- yellow
    '#89B4FA', -- blue
    '#F5C2E7', -- magenta
    '#94E2D5', -- cyan
    '#BAC2DE', -- white
  },
  brights = {
    '#585B70', -- black
    '#F38BA8', -- red
    '#A6E3A1', -- green
    '#F9E2AF', -- yellow
    '#89B4FA', -- blue
    '#F5C2E7', -- magenta
    '#94E2D5', -- cyan
    '#A6ADC8', -- white
  },

  -- Tab bar colors
  tab_bar = {
    background = '#11111B',
    active_tab = {
      bg_color = '#CBA6F7',
      fg_color = '#11111B',
    },
    inactive_tab = {
      bg_color = '#181825',
      fg_color = '#CDD6F4',
    },
    inactive_tab_hover = {
      bg_color = '#181825',
      fg_color = '#CDD6F4',
    },
    new_tab = {
      bg_color = '#11111B',
      fg_color = '#CDD6F4',
    },
    new_tab_hover = {
      bg_color = '#181825',
      fg_color = '#CDD6F4',
    },
  },
}

return {
  -- Font configuration
  font = wezterm.font('Fira Code', { weight = 'Regular' }),
  font_size = 16,

  -- Color scheme
  color_schemes = {
    ['Catppuccin Mocha'] = catppuccin_mocha,
  },
  color_scheme = 'Catppuccin Mocha',

  -- Window configuration
  window_padding = {
    left = 10,
    right = 10,
    top = 10,
    bottom = 10,
  },
  window_decorations = 'NONE', -- Hide window decorations (like kitty hide_window_decorations)
  window_background_opacity = 1.0,

  -- Background image (scaled to cover, similar to kitty cscaled)
  window_background_image = wezterm.config_dir .. '/wallpaper.png',
  window_background_image_hsb = {
    brightness = 1.0,
    hue = 1.0,
    saturation = 1.0,
  },

  -- Shell
  default_prog = { 'fish' },

  -- Tab bar
  enable_tab_bar = true,
  tab_bar_at_bottom = false,
  use_fancy_tab_bar = true,
  hide_tab_bar_if_only_one_tab = true, -- Hide tab bar when only one tab (cleaner look)

  -- Scrollback
  scrollback_lines = 10000,

  -- Enable CSI-u (fixterms/kitty) keyboard protocol for proper modifier key handling
  -- This allows applications to distinguish Shift+Enter from Enter
  enable_csi_u_key_encoding = true,

  -- Key bindings: send CSI-u escape sequences for modified Enter
  keys = {
    -- Shift+Enter: send \x1b[13;2u (CSI u format: ESC [ keycode ; modifiers u)
    -- 13 = Enter keycode, 2 = Shift modifier
    { key = 'Enter', mods = 'SHIFT', action = wezterm.action.SendString('\x1b[13;2u') },
    -- Ctrl+Enter: send \x1b[13;5u (5 = Ctrl modifier)
    { key = 'Enter', mods = 'CTRL', action = wezterm.action.SendString('\x1b[13;5u') },
    -- Alt+Enter: send \x1b[13;3u (3 = Alt modifier)
    { key = 'Enter', mods = 'ALT', action = wezterm.action.SendString('\x1b[13;3u') },
  },

  -- Startup behavior (similar to kitty startup_session)
  -- WezTerm doesn't have exact equivalent, but we can set default working directory
  default_cwd = wezterm.home_dir,
}
