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

-- Maximize window on startup
local mux = wezterm.mux

wezterm.on('gui-startup', function(cmd)
  local tab, pane, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)

-- Maximize window when GUI attaches (handles cases where gui-startup doesn't fire)
wezterm.on('gui-attached', function(domain)
  local window = mux.get_active_window()
  if window then
    window:gui_window():maximize()
  end
end)

return {
  font = wezterm.font_with_fallback({
    { family = 'FiraCode Nerd Font Mono', weight = 'Regular' },
    { family = 'FiraCode Nerd Font', weight = 'Regular' },
    { family = 'Fira Code', weight = 'Regular' },
    'JetBrainsMono Nerd Font',
    'DejaVu Sans',
    'Noto Color Emoji',
  }),
  font_size = 16,
  warn_about_missing_glyphs = false,
  -- Ensure proper rendering of icons and symbols
  freetype_load_target = 'Light',
  freetype_render_target = 'HorizontalLcd',

  -- Font rules for bold/italic variants
  font_rules = {
    {
      intensity = 'Bold',
      font = wezterm.font_with_fallback({
        { family = 'FiraCode Nerd Font', weight = 'Bold' },
        { family = 'FiraCode Nerd Font Mono', weight = 'Bold' },
        { family = 'Fira Code', weight = 'Bold' },
      }),
    },
  },

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

  window_decorations = 'NONE',
  window_background_opacity = 1.0,


  window_background_image = wezterm.config_dir .. '/wallpaper.png',
  window_background_image_hsb = {
    brightness = 1.0,
    hue = 1.0,
    saturation = 1.0,
  },

  default_prog = { 'fish' },

  hide_tab_bar_if_only_one_tab = true,
  enable_tab_bar = false,

  scrollback_lines = 10000,

  -- Enable kitty graphics protocol for inline image/video display
  -- This allows tools like ani-cli to display video frames in the terminal
  enable_kitty_graphics = true,

  -- Enable CSI-u (fixterms/kitty) keyboard protocol for proper modifier key handling
  -- This allows applications to distinguish Shift+Enter from Enter
  enable_csi_u_key_encoding = true,

  -- Key bindings
  keys = {
    -- Shift+Enter: send newline character for multi-line input
    { key = 'Enter', mods = 'SHIFT', action = wezterm.action.SendString('\n') },
    -- Ctrl+Enter: send \x1b[13;5u (5 = Ctrl modifier) for apps that need it
    { key = 'Enter', mods = 'CTRL', action = wezterm.action.SendString('\x1b[13;5u') },
    -- Alt+Enter: send \x1b[13;3u (3 = Alt modifier)
    { key = 'Enter', mods = 'ALT', action = wezterm.action.SendString('\x1b[13;3u') },
    -- Ctrl+Shift+S: open tmux and show session chooser (mimics tmux Leader+S)
    { key = 's', mods = 'CTRL|SHIFT', action = wezterm.action.SendString(os.getenv('HOME') .. '/.dotfiles/bin/tmux-session-chooser\n') },
    -- Ctrl+Shift+Up/Down: send xterm sequences for tmux copy mode navigation
    { key = 'UpArrow', mods = 'CTRL|SHIFT', action = wezterm.action.SendString('\x1b[1;6A') },
    { key = 'DownArrow', mods = 'CTRL|SHIFT', action = wezterm.action.SendString('\x1b[1;6B') },
  },

  -- Startup behavior (similar to kitty startup_session)
  -- WezTerm doesn't have exact equivalent, but we can set default working directory
  default_cwd = wezterm.home_dir,

  -- Set very large initial window size to approximate maximized state
  -- This helps when windows are created in existing instances (where gui-startup doesn't fire)
  initial_cols = 300,
  initial_rows = 100,
}
