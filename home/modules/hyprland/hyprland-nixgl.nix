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

  hyprlandLowercaseAlias = pkgs.writeShellScriptBin "hyprland" ''
    exec ${hyprlandFlake}/bin/Hyprland "$@"
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
