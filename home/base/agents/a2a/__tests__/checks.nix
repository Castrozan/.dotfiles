{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  a2aInstallActivation = cfg.home.activation.installA2aMcpServer.data;
in
{
  domain-agents-a2a-install-is-time-bounded =
    mkEvalCheck "domain-agents-a2a-install-is-time-bounded"
      (lib.hasInfix "/bin/timeout " a2aInstallActivation)
      "The a2a MCP server install must run under a timeout. It shells out to `npm install -g` against a live registry, and an unbounded call that stalls rather than fails wedges the whole switch with the new home generation already linked and the system profile still on the old one, reporting nothing because nothing failed";

  domain-agents-a2a-install-must-not-swallow-its-own-failure =
    mkEvalCheck "domain-agents-a2a-install-must-not-swallow-its-own-failure"
      (!lib.hasInfix "|| true" a2aInstallActivation)
      "The a2a MCP server install must NOT end in `|| true`, and this check exists to stop a well-meaning sweep from adding one. a2a is the transport the fleet's stewards coordinate over, so a silently skipped install does not degrade to a missing nicety, it produces a machine that activates green and cannot talk to its peers. Bounding the call is right; swallowing its failure is not. Steps whose failure only costs a best-effort nicety take `|| true`; steps the machine's continued operation depends on must fail loudly";
}
