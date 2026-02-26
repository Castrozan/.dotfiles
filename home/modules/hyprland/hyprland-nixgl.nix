{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;

  hyprlandWrapped = nixglWrap.wrapWithNixGLIntel {
    package = hyprlandFlake;
    binaries = [ "Hyprland" ];
  };

  nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;

  hyprlandLowercaseAlias = pkgs.writeShellScriptBin "hyprland" ''
    exec ${nixGLWrapper}/bin/nixGLIntel ${hyprlandFlake}/bin/Hyprland "$@"
  '';

  hyprlandWithAliases = pkgs.symlinkJoin {
    name = "hyprland-with-aliases";
    paths = [
      hyprlandLowercaseAlias
      hyprlandWrapped
    ];
  };
in
{
  home.packages = [ hyprlandWithAliases ];
}
