{ inputs, system }:
let
  inherit (import ./channels.nix { inherit inputs system; }) pkgs latest;
  inherit (pkgs) lib;
in
{
  codex = import ../../agent-harness/harnesses/codex/unwrapped-package.nix {
    inherit
      pkgs
      lib
      latest
      inputs
      ;
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

  wezterm = import ../../machine-configuration/terminal/emulators/wezterm/patched-wezterm.nix {
    inherit latest;
  };
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  devenv =
    import ../../machine-configuration/development/development-environments/devenv-cached-package.nix
      {
        inherit pkgs inputs;
      };
}
