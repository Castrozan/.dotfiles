{ lib, ... }:
let
  selectedTheme = import ../selected-theme.nix;

  themeColorsToml = selectedTheme.colorsToml;

  themeIsLight = selectedTheme.isLight;

  selectedWallpaperPath = selectedTheme.wallpaperPath;

  removeHashFromColor = color: lib.removePrefix "#" color;

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
  home.activation.applyMacosThemeAppearance = lib.hm.dag.entryAfter [
    "writeBoundary"
  ] macosAppearanceActivationScript;
}
