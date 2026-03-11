local wezterm = require 'wezterm'

local catppuccin_mocha = {
  foreground = '#CDD6F4',
  background = '#0F0D0E',
  cursor_bg = '#F5E0DC',
  cursor_fg = '#1E1E2E',
  selection_bg = '#F5E0DC',
  selection_fg = '#1E1E2E',

  ansi = {
    '#9399B2',
    '#F38BA8',
    '#A6E3A1',
    '#F9E2AF',
    '#89B4FA',
    '#F5C2E7',
    '#94E2D5',
    '#BAC2DE',
  },
  brights = {
    '#A6ADC8',
    '#F38BA8',
    '#A6E3A1',
    '#F9E2AF',
    '#89B4FA',
    '#F5C2E7',
    '#94E2D5',
    '#A6ADC8',
  },
}

local mux = wezterm.mux
wezterm.on('gui-startup', function(cmd)
  local tab, pane, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)

wezterm.on('gui-attached', function(domain)
  local window = mux.get_active_window()
  if window then
    window:gui_window():maximize()
  end
end)

return {
  font = wezterm.font_with_fallback({
    'FiraCode Nerd Font Mono',
    'Noto Color Emoji',
  }),
  font_size = wezterm.target_triple:find('darwin') and 19 or 16,

  color_schemes = {
    ['Catppuccin Mocha'] = catppuccin_mocha,
  },
  color_scheme = 'Catppuccin Mocha',

  window_padding = {
    left = 10,
    right = 10,
    top = 10,
    bottom = 10,
  },

  max_fps = 120,
  window_decorations = 'NONE',
  window_background_opacity = 0.6,
  enable_tab_bar = false,
  hide_tab_bar_if_only_one_tab = true,

  warn_about_missing_glyphs = false,
  freetype_load_target = 'Light',
  scrollback_lines = 10000,
  default_prog = { wezterm.target_triple:find('darwin') and '/run/current-system/sw/bin/fish' or 'fish' },
  default_cwd = wezterm.home_dir,

  enable_csi_u_key_encoding = true,

  bypass_mouse_reporting_modifiers = 'CTRL',

  mouse_bindings = {
    {
      event = { Up = { streak = 1, button = 'Left' } },
      mods = 'CTRL',
      action = wezterm.action.OpenLinkAtMouseCursor,
    },
  },

  keys = {
    { key = 'Enter', mods = 'SHIFT', action = wezterm.action.SendString('\n') },
    { key = 'Enter', mods = 'CTRL', action = wezterm.action.SendString('\x1b[13;5u') },
    { key = 'Enter', mods = 'ALT', action = wezterm.action.SendString('\x1b[13;3u') },
    { key = 's', mods = 'CTRL|SHIFT', action = wezterm.action.SendString(os.getenv('HOME') .. '/.dotfiles/bin/tmux-session-chooser\n') },
    { key = 'UpArrow', mods = 'CTRL|SHIFT', action = wezterm.action.SendString('\x1b[1;6A') },
    { key = 'DownArrow', mods = 'CTRL|SHIFT', action = wezterm.action.SendString('\x1b[1;6B') },
  },

  initial_cols = 300,
  initial_rows = 100,

  window_close_confirmation = 'NeverPrompt',
}
