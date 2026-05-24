{ pkgs, lib, ... }:
let
  selectedThemeName = "kanagawa";

  themesDirectory = ../../../../static/themes;

  themeColorsToml = builtins.fromTOML (
    builtins.readFile (themesDirectory + "/${selectedThemeName}/colors.toml")
  );

  themeIsLight = builtins.pathExists (themesDirectory + "/${selectedThemeName}/light.mode");

  themeBackgroundFileNames = builtins.attrNames (
    builtins.readDir (themesDirectory + "/${selectedThemeName}/backgrounds")
  );

  sortedBackgroundFileNames = builtins.sort (a: b: a < b) themeBackgroundFileNames;

  firstBackgroundFileName = builtins.head sortedBackgroundFileNames;

  selectedWallpaperPath =
    themesDirectory + "/${selectedThemeName}/backgrounds/${firstBackgroundFileName}";

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

  macosAppearanceActivationScript = import ./macos-appearance-activation.nix {
    inherit
      lib
      themeColorsToml
      themeIsLight
      selectedWallpaperPath
      removeHashFromColor
      ;
  };
in
{
  stylix = stylixConfiguration;

  programs.wezterm.extraConfig = lib.mkBefore weztermThemeExtraConfig;

  home.activation.injectVscodeThemeColors = lib.hm.dag.entryAfter [
    "writeBoundary"
  ] vscodeThemeInjectionActivationScript;

  home.activation.applyMacosThemeAppearance = lib.hm.dag.entryAfter [
    "writeBoundary"
  ] macosAppearanceActivationScript;
}
