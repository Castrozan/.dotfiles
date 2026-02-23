{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  weztermPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.wezterm;
    binaries = [
      "wezterm"
      "wezterm-gui"
    ];
  };
in
{
  home.file.".config/wezterm/wallpaper.png".source = ../../static/wallpaper.png;

  programs.wezterm = {
    enable = true;
    package = weztermPackage;
    extraConfig = builtins.readFile ../../.config/wezterm/wezterm.lua;
  };
}
