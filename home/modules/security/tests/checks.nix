{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
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

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
in
{
  domain-security-gpg-agent = mkEvalCheck "domain-security-gpg-agent" (
    cfg.programs.gpg.enable && cfg.services.gpg-agent.enable
  ) "gpg and gpg-agent should be enabled";

  domain-security-password-store = mkEvalCheck "domain-security-password-store" (
    cfg.programs.password-store.enable && hasService "password-store-git-sync"
  ) "password-store should be enabled with sync service";

  domain-security-agenix-secrets = mkEvalCheck "domain-security-agenix-secrets" (
    builtins.length (builtins.attrNames cfg.age.secrets) > 0 && hasFile ".secrets/source-secrets.sh"
  ) "agenix secrets should be configured";
}
