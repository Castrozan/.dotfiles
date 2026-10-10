{ inputs, system }:
let
  inherit (import ./channels.nix { inherit inputs system; }) pkgs;
  inherit (pkgs) lib;
in
{
  herdr = import ../../machine-configuration/terminal/workspace-manager/herdr/herdr-package.nix {
    inherit pkgs inputs;
  };

  herdr-agent-resume =
    import ../../machine-configuration/terminal/workspace-manager/herdr/herdr-agent-resume-package.nix
      {
        inherit pkgs lib;
      };

  herdr-annotate =
    import
      ../../machine-configuration/terminal/workspace-manager/herdr/annotation/herdr-annotate-package.nix
      {
        inherit pkgs lib inputs;
      };
}
