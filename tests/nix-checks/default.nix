{
  pkgs,
  lib,
  inputs,
  self,
}:
let
  domainModuleChecks = import ./domain-modules.nix { inherit pkgs lib inputs; };

  homeManagerModuleChecks = import ./home-manager-modules.nix {
    inherit
      pkgs
      lib
      inputs
      self
      ;
  };

  claudeChecks = import ../../home/modules/claude/tests/checks.nix {
    inherit
      pkgs
      lib
      inputs
      self
      ;
  };

  codexChecks = import ../../home/modules/codex/tests/checks.nix {
    inherit
      pkgs
      lib
      inputs
      self
      ;
  };

  openclawChecks = import ../../home/modules/openclaw/tests/checks.nix {
    inherit
      pkgs
      lib
      inputs
      self
      ;
  };

  openclawConfigChecks = import ../../home/modules/openclaw/tests/nix-config-checks.nix {
    inherit
      pkgs
      lib
      inputs
      self
      ;
  };
in
domainModuleChecks
// homeManagerModuleChecks
// claudeChecks
// codexChecks
// openclawChecks
// openclawConfigChecks
