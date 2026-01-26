# Hyprland for non-NixOS (e.g., Ubuntu with home-manager standalone)
# Requires nixGL wrapper to access host system OpenGL libraries
{ pkgs, inputs, ... }:
let
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
  nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;

  hyprland-gl = pkgs.writeShellScriptBin "Hyprland" ''
    exec ${nixGLWrapper}/bin/nixGLIntel ${hyprlandFlake}/bin/Hyprland "$@"
  '';

  hyprland-lowercase-gl = pkgs.writeShellScriptBin "hyprland" ''
    exec ${nixGLWrapper}/bin/nixGLIntel ${hyprlandFlake}/bin/Hyprland "$@"
  '';

  hyprctl-gl = pkgs.writeShellScriptBin "hyprctl" ''
    exec ${hyprlandFlake}/bin/hyprctl "$@"
  '';

  hyprland-wrapped = pkgs.symlinkJoin {
    name = "hyprland-wrapped";
    paths = [
      hyprland-gl
      hyprland-lowercase-gl
      hyprctl-gl
      hyprlandFlake
    ];
  };
in
{
  home.packages = [ hyprland-wrapped ];
}
