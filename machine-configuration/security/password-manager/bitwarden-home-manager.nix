{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config.home) homeDirectory;
  applicationDataRoot = "${homeDirectory}/.local/share/bitwarden-cli";

  bitwardenAccountModule =
    { name, ... }:
    {
      options = {
        server = lib.mkOption {
          type = lib.types.nullOr lib.types.str;
          default = null;
          description = "Base URL of the Bitwarden or Vaultwarden server this account authenticates against; null uses the public Bitwarden cloud. Declare an employer-hosted server from private-config so its host name never lands in the public repository.";
        };
        clientIdSecret = lib.mkOption {
          type = lib.types.str;
          description = "Basename under ~/.secrets of the agenix secret holding this account's API key client id.";
        };
        clientSecretSecret = lib.mkOption {
          type = lib.types.str;
          description = "Basename under ~/.secrets of the agenix secret holding this account's API key client secret.";
        };
        masterPasswordSecret = lib.mkOption {
          type = lib.types.str;
          description = "Basename under ~/.secrets of the agenix secret holding this account's master password.";
        };
        applicationDataDirectory = lib.mkOption {
          type = lib.types.str;
          default = "${applicationDataRoot}/${name}";
          description = "Writable per-account BITWARDENCLI_APPDATA_DIR the bitwarden-cli keeps its data.json, session and vault cache under. This module only ensures the directory exists; it is never a read-only nix-store symlink, so each account holds an independent server and session and switching accounts never corrupts the other's config.";
        };
      };
    };

  bitwardenConfiguration = config.custom.bitwardenCli;
  declaredAccounts = bitwardenConfiguration.accounts;

  accountRegistryContent = builtins.toJSON (
    lib.mapAttrs (_: account: {
      inherit (account)
        server
        applicationDataDirectory
        clientIdSecret
        clientSecretSecret
        masterPasswordSecret
        ;
    }) declaredAccounts
  );

  bitwardenSessionHelper = pkgs.writeShellApplication {
    name = "bw-session";
    runtimeInputs = [
      pkgs.bitwarden-cli
      pkgs.jq
      pkgs.coreutils
    ];
    text = builtins.readFile ./scripts/bw-session.sh;
  };

  makeAccountScopedWrapper =
    accountName: account:
    pkgs.writeShellApplication {
      name = "bw-${accountName}";
      runtimeInputs = [ pkgs.bitwarden-cli ];
      text = ''
        export BITWARDENCLI_APPDATA_DIR=${lib.escapeShellArg account.applicationDataDirectory}
        exec bw "$@"
      '';
    };

  accountScopedWrappers = lib.mapAttrsToList makeAccountScopedWrapper declaredAccounts;

  ensureApplicationDataDirectoriesScript = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (
      _: account:
      "$DRY_RUN_CMD ${pkgs.coreutils}/bin/mkdir -p ${lib.escapeShellArg account.applicationDataDirectory}"
    ) declaredAccounts
  );
in
{
  options.custom.bitwardenCli.accounts = lib.mkOption {
    type = lib.types.attrsOf (lib.types.submodule bitwardenAccountModule);
    default = { };
    description = "Bitwarden accounts the bitwarden-cli can hold side by side, each isolated in its own writable BITWARDENCLI_APPDATA_DIR with its own pinned server and agenix-backed API key and master password. The public repository declares only the personal account on the default cloud; an employer account is added from private-config so its server host stays private. Each declared account gets a bw-<name> wrapper that runs bw against that account's data directory, and `bw-session <name>` (defaulting to personal) mints an unlocked session for it without a prompt.";
  };

  config = {
    custom.bitwardenCli.accounts.personal = {
      server = null;
      clientIdSecret = "bitwarden-client-id";
      clientSecretSecret = "bitwarden-client-secret";
      masterPasswordSecret = "bitwarden-master-password";
    };

    programs.bash.shellAliases = {
      bwu = "bw-session personal";
    };

    home = {
      packages = [
        pkgs.bitwarden-cli
        bitwardenSessionHelper
      ]
      ++ accountScopedWrappers;

      file.".config/bitwarden-cli/accounts.json".text = accountRegistryContent;

      activation.ensureBitwardenApplicationDataDirectories = lib.hm.dag.entryAfter [
        "writeBoundary"
      ] ensureApplicationDataDirectoriesScript;
    };
  };
}
