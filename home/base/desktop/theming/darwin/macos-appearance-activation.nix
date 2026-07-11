{
  lib,
  themeColorsToml,
  themeIsLight,
  selectedWallpaperPath,
  removeHashFromColor,
}:
let
  themeAccentColorHex = removeHashFromColor themeColorsToml.accent;
in
''
  export DESIRED_DARK_MODE=${if themeIsLight then "\"false\"" else "\"true\""}
  export WALLPAPER_PATH=${lib.escapeShellArg selectedWallpaperPath}
  export THEME_ACCENT_HEX=${lib.escapeShellArg themeAccentColorHex}
  export ACCENT_FROM_HEX_SCRIPT=${./macos-accent-color-from-hex.py}
  ${builtins.readFile ./apply-macos-theme-appearance.sh}
''
