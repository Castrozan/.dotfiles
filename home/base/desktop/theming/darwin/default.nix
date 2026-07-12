{ pkgs, lib, ... }:
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
  home.activation.applyMacosThemeAppearance = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin (
    lib.hm.dag.entryAfter [ "writeBoundary" ] macosAppearanceActivationScript
  );

  home.file = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    ".config/hypr-theme/current/theme/colors.toml".source = selectedTheme.colorsTomlPath;
    ".config/hypr-theme/current/theme.name".text = selectedTheme.name;
  };
}
