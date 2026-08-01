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

  ingestProducerSecretName = "credentials/ingest-producer-secret";

  gpgKeyImportActivation = cfg.home.activation.importGpgPrivateKeyFromAgenix.data;
in
{
  domain-security-gpg-key-import-is-time-bounded =
    mkEvalCheck "domain-security-gpg-key-import-is-time-bounded"
      (lib.hasInfix "/bin/timeout " gpgKeyImportActivation)
      "The gpg key import must run under a timeout. Every gpg invocation in it talks to gpg-agent, and this configuration sets pinentry-curses, which needs a TTY that activation does not have, so an agent that decides to prompt blocks forever rather than returning non-zero. An unbounded step wedges the whole switch with the new home generation already linked and the system profile still on the old one, and nothing reports it because nothing failed";

  domain-security-gpg-key-import-tolerates-its-own-failure =
    mkEvalCheck "domain-security-gpg-key-import-tolerates-its-own-failure"
      (lib.hasInfix "|| true" gpgKeyImportActivation)
      "The gpg key import must end in `|| true`, because home-manager runs activation under set -e, so a step cut short by its own timeout would otherwise abort activation before any later generation step runs; importing a key is best-effort and must never be able to fail a switch";

  domain-security-ingest-producer-secret-materialises =
    mkEvalCheck "domain-security-ingest-producer-secret-materialises"
      (
        (cfg.age.secrets.${ingestProducerSecretName}.path or null)
        == "${cfg.home.homeDirectory}/.secrets/ingest-producer-secret"
      )
      "the contracted usage publisher reads ~/.secrets/ingest-producer-secret at launch and refuses to publish when it is absent; agenix only declares a secret whose .age file reaches the flake source, so an untracked or renamed secrets/credentials/ingest-producer-secret.age silently kills the ingestion producer on every machine";

  domain-security-gpg-agent = mkEvalCheck "domain-security-gpg-agent" (
    cfg.programs.gpg.enable && cfg.services.gpg-agent.enable
  ) "gpg and gpg-agent should be enabled";

  domain-security-bitwarden = mkEvalCheck "domain-security-bitwarden" (
    hasPackage "bitwarden-cli" && hasPackage "bw-session"
  ) "bitwarden-cli and the bw-session helper should be installed";

  domain-security-agenix-secrets = mkEvalCheck "domain-security-agenix-secrets" (
    builtins.length (builtins.attrNames cfg.age.secrets) > 0 && hasFile ".secrets/source-secrets.sh"
  ) "agenix secrets should be configured";

  domain-security-opencode-api-key-materialises =
    mkEvalCheck "domain-security-opencode-api-key-materialises"
      (
        (cfg.age.secrets."api-keys/opencode-api-key".path or null)
        == "${cfg.home.homeDirectory}/.secrets/opencode-api-key"
      )
      "opencode defaults to a model on the paid opencode-go plan and its wrapper reads this exact path to authenticate; agenix only declares a secret whose .age file reaches the flake source, so an untracked secrets/api-keys/opencode-api-key.age turns every default-model turn into an auth failure while the free models keep working and hide the cause";
}
