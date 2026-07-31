{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;
in
import ./service-checks.nix {
  inherit
    mkEvalCheck
    helpers
    self
    ;
}
// import ./discord-channel-access-checks.nix {
  inherit
    lib
    mkEvalCheck
    helpers
    self
    ;
}
// import ./harness-checks.nix {
  inherit
    pkgs
    mkEvalCheck
    helpers
    self
    ;
}
// import ./channel-sidecar-checks.nix {
  inherit
    mkEvalCheck
    helpers
    self
    ;
}
