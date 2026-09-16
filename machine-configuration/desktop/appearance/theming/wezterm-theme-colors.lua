local themeTerminalColors = config.colors or {}
themeTerminalColors.ansi = {
  "@color0@",
  "@color1@",
  "@color2@",
  "@color3@",
  "@color4@",
  "@color5@",
  "@color6@",
  "@color7@",
}
themeTerminalColors.brights = {
  "@color8@",
  "@color9@",
  "@color10@",
  "@color11@",
  "@color12@",
  "@color13@",
  "@color14@",
  "@color15@",
}
themeTerminalColors.cursor_bg = "@cursor@"
themeTerminalColors.cursor_fg = "@background@"
themeTerminalColors.selection_bg = "@selection_background@"
themeTerminalColors.selection_fg = "@selection_foreground@"
config.colors = themeTerminalColors
