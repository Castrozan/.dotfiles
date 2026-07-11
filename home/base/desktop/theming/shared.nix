{ pkgs, lib, ... }:
let
  selectedTheme = import ./selected-theme.nix;

  themeColorsToml = selectedTheme.colorsToml;

  themeIsLight = selectedTheme.isLight;

  selectedWallpaperPath = selectedTheme.wallpaperPath;

  removeHashFromColor = color: lib.removePrefix "#" color;

  stylixConfiguration = import ./stylix-configuration.nix {
    inherit
      pkgs
      themeColorsToml
      themeIsLight
      selectedWallpaperPath
      removeHashFromColor
      ;
  };

  weztermThemeExtraConfig = import ./wezterm-theme-colors.nix {
    inherit lib themeColorsToml;
  };

  vscodeThemeInjectionActivationScript = import ./vscode-theme-colors.nix {
    inherit pkgs themeColorsToml;
  };
in
{
  stylix = stylixConfiguration;

  programs.wezterm.extraConfig = lib.mkBefore weztermThemeExtraConfig;

  home.activation.injectVscodeThemeColors = lib.hm.dag.entryAfter [
    "writeBoundary"
  ] vscodeThemeInjectionActivationScript;
}
