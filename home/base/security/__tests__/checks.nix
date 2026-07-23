{
  pkgs,
  lib,
  inputs,
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

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasPackage =
    needle: builtins.any (package: lib.hasInfix needle (package.name or "")) cfg.home.packages;
in
{
  domain-security-gpg-agent = mkEvalCheck "domain-security-gpg-agent" (
    cfg.programs.gpg.enable && cfg.services.gpg-agent.enable
  ) "gpg and gpg-agent should be enabled";

  domain-security-bitwarden = mkEvalCheck "domain-security-bitwarden" (
    hasPackage "bitwarden-cli" && hasPackage "bw-session"
  ) "bitwarden-cli and the bw-session helper should be installed";

  domain-security-agenix-secrets = mkEvalCheck "domain-security-agenix-secrets" (
    builtins.length (builtins.attrNames cfg.age.secrets) > 0 && hasFile ".secrets/source-secrets.sh"
  ) "agenix secrets should be configured";
}
