{ pkgs, inputs, ... }:
let
  isNixOS = builtins.pathExists /etc/NIXOS;

  # On non-NixOS we need nixGL to provide OpenGL support
  weztermPackage = if isNixOS then
    pkgs.wezterm
  else
    let
      nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLDefault;
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
          pkgs.wezterm
        ];
      };
    in
    wezterm-wrapped;
in
{
  home.file.".config/wezterm/wallpaper.png".source = ../../static/wallpaper.png;

  programs.wezterm = {
    enable = true;
    package = weztermPackage;
    extraConfig = builtins.readFile ../../.config/wezterm/wezterm.lua;
  };
}
