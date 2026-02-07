{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  # On non-NixOS we need nixGL to provide OpenGL support
  # Using nixGLIntel (Mesa) directly instead of nixGLDefault to avoid
  # impure IFD that rebuilds on every evaluation (~3s overhead)
  weztermPackage =
    if isNixOS then
      pkgs.wezterm
    else
      let
        nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;
        wezterm-gl = pkgs.writeShellScriptBin "wezterm" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${pkgs.wezterm}/bin/wezterm "$@"
        '';
        wezterm-gui-gl = pkgs.writeShellScriptBin "wezterm-gui" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${pkgs.wezterm}/bin/wezterm-gui "$@"
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
