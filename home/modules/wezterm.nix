{ pkgs, inputs, ... }:
let
  # nixGLDefault auto-detects the right OpenGL implementation
  # Falls back to nixGLMesa for AMD/Intel or nixGLNvidia for NVIDIA
  nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLDefault;

  # Wrap wezterm with nixGL for OpenGL support on non-NixOS
  wezterm-gl = pkgs.writeShellScriptBin "wezterm" ''
    exec ${nixGLWrapper}/bin/nixGL ${pkgs.wezterm}/bin/wezterm "$@"
  '';

  wezterm-gui-gl = pkgs.writeShellScriptBin "wezterm-gui" ''
    exec ${nixGLWrapper}/bin/nixGL ${pkgs.wezterm}/bin/wezterm-gui "$@"
  '';

  wezterm-wrapped = pkgs.symlinkJoin {
    name = "wezterm-wrapped";
    paths = [
      wezterm-gl
      wezterm-gui-gl
      pkgs.wezterm # For terminfo and other resources
    ];
  };
in
{
  home.file.".config/wezterm/wallpaper.png".source = ../../static/wallpaper.png;

  programs.wezterm = {
    enable = true;
    package = wezterm-wrapped;
    extraConfig = builtins.readFile ../../.config/wezterm/wezterm.lua;
  };
}
