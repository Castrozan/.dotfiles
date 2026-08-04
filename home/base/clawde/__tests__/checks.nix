{
  helpers,
  pkgs,
  lib,
  self,
  ...
}:
let
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
    lib
    mkEvalCheck
    helpers
    self
    ;
}
// import ./a2a-peer-checks.nix {
  inherit
    lib
    mkEvalCheck
    helpers
    self
    ;
}
