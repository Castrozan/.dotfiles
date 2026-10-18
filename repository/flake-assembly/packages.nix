{ inputs, system }:
let
  inherit (import ./channels.nix { inherit inputs system; }) pkgs;
  inherit (pkgs) lib;
in
{
  wellput-plugin = import ../../agent-harness/agent-instructions/wellput-plugin { inherit pkgs; };

  devenv =
    import ../../machine-configuration/development/development-environments/devenv-cached-package.nix
      {
        inherit pkgs inputs;
      };

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
