{
  helpers,
  inputs,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  system = self.nixosConfigurations.chise;
  settings = system.config.services.arrStack;
  inherit (system.config.systemd) services;
  policyServices = [
    "jellyfin-library-access-provisioner"
    "jellyseerr-account-permission-provisioner"
    "jellyseerr-private-request-routing-provisioner"
  ];
in
{
  chise-arr-stack-imports-the-external-module =
    mkEvalCheck "chise-arr-stack-imports-the-external-module"
      (
        settings.enable
        && builtins.any (
          declaration: lib.hasPrefix "${inputs.arr-stack}/" (toString declaration)
        ) system.options.services.arrStack.enable.declarations
        && !(builtins.pathExists (self.outPath + "/machine-configuration/media/arr-stack"))
        && !(builtins.pathExists (self.outPath + "/machine-configuration/media/manga-streaming"))
      )
      "Chise must import the pinned external implementation without retaining a second copy in dotfiles";

  chise-arr-stack-preserves-storage-and-supervision =
    mkEvalCheck "chise-arr-stack-preserves-storage-and-supervision"
      (
        settings.directory == "/home/zanoni/arr-stack"
        && settings.userId == 1000
        && settings.groupId == 100
        && settings.hardwareAcceleration == "nvidia"
        && system.config.custom.arrStackOnDemandSupervisor.keepChainAlwaysOn
        && builtins.elem settings.dataMountUnit services.arr-download-cleanup.bindsTo
        && builtins.elem "home-manager-zanoni.service" services.arr-stack-front-ends-compose.requires
        && builtins.elem "arr-stack-drive-guard.service" services.miwayomi-compose.requires
      )
      "The external module must retain Chise's existing media owner, GPU, mount guard and always-on download chain";

  chise-arr-stack-preserves-private-library-policy =
    mkEvalCheck "chise-arr-stack-preserves-private-library-policy"
      (
        settings.accounts.privateLibraryAccounts == [
          "private-requests"
          "jellyseerr"
        ]
        && settings.accounts.administratorAccounts == [ "jellyseerr" ]
        &&
          settings.accounts.advancedRequestAccounts == [
            "lucas"
            "rogerio"
          ]
        && builtins.all (
          name:
          services.${name}.environment.ARR_USERS_LIBRARY_ROOT == "/media"
          && services.${name}.environment.ARR_ACCOUNT_POLICY_FILE != ""
        ) policyServices
        && settings.secrets.jellyfinApiKey.file == system.config.age.secrets.jellyfin-admin-api-key.path
      )
      "Chise's private library allowlists and original Jellyfin media paths must reach every account reconciler";

  chise-arr-stack-preserves-secret-reconciliation =
    mkEvalCheck "chise-arr-stack-preserves-secret-reconciliation"
      (
        builtins.elem settings.secrets.qbittorrentPassword.source services.arr-config-provisioner.restartTriggers
        && builtins.elem settings.secrets.extensionRepositories.source services.miwayomi-extension-repositories.restartTriggers
        && builtins.elem settings.secrets.smtpPassword.source services.jellyseerr-email-notifications.restartTriggers
        &&
          system.config.custom.stremioStreamingServer.streamCacheDirectory
          == "${settings.directory}/data/stremio-cache"
      )
      "Encrypted secret changes must reconcile the imported services while the shared disk still owns the streaming cache";
}
