{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  nixosCfg = self.nixosConfigurations.chise.config;
in
import ./chise-arr-stack-host-integration.nix { inherit lib mkEvalCheck nixosCfg; }
