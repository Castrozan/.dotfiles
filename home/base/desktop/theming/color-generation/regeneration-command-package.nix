{ pkgs }:
let
  themeColorsFromWallpaperGenerator = import ./package.nix {
    inherit pkgs;
    binName = "theme-colors-from-wallpaper";
  };
in
pkgs.writeShellApplication {
  name = "theme-regenerate-wallpaper-derived-colors";
  runtimeInputs = [
    pkgs.coreutils
    pkgs.findutils
    pkgs.git
    themeColorsFromWallpaperGenerator
  ];
  text = builtins.readFile ./regenerate_wallpaper_derived_colors.sh;
}
