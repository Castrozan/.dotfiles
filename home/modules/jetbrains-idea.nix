{
  pkgs,
  isNixOS,
  ...
}:
let
  ideaPackage = pkgs.jetbrains.idea;

  ideaWaylandVmOptions = pkgs.writeText "idea-wayland.vmoptions" ''
    -Dawt.toolkit.name=WLToolkit
  '';

  ideaWithWayland = pkgs.writeShellScriptBin "idea" ''
    export IDEA_VM_OPTIONS="${ideaWaylandVmOptions}"
    exec ${ideaPackage}/bin/idea "$@"
  '';

  ideaWrapped = pkgs.symlinkJoin {
    name = "jetbrains-idea-wrapped";
    paths = [
      ideaWithWayland
      ideaPackage
    ];
  };

  finalPackage = if isNixOS then ideaPackage else ideaWrapped;
in
{
  home.packages = [ finalPackage ];
}
