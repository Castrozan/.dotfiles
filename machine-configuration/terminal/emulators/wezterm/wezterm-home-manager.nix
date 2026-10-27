{
  lib,
  pkgs,
  inputs,
  isNixOS,
  latest,
  ...
}:
let
  nixglWrap = import ../../../../repository/nix-library/nixgl-wrap.nix {
    inherit pkgs inputs isNixOS;
  };

  patchedWezterm = import ./patched-wezterm.nix { inherit latest; };

  weztermAfterNixGL = nixglWrap.wrapWithNixGLIntel {
    package = patchedWezterm;
    binaries = [
      "wezterm"
      "wezterm-gui"
    ];
  };

in
{
  home.file.".config/wezterm/wallpaper.png".source =
    ../../../desktop/appearance/theming/wallpapers/artwork/wallpaper.png;

  xdg.configFile."xdg-terminals.list" = lib.mkIf isNixOS { source = ./xdg-terminals.list; };

  programs.wezterm = {
    enable = true;
    package = weztermAfterNixGL;
    extraConfig = builtins.readFile ./program-configuration/wezterm.lua;
  };
}
