{
  pkgs,
  lib,
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  evalProvisioner =
    settings:
    (lib.evalModules {
      specialArgs = { inherit pkgs; };
      modules = [
        ../../../nixos/modules/arr-config-provisioner
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.arrConfigProvisioner = settings;
        }
      ];
    }).config;

  baseSettings = {
    enable = true;
    stackHomeDirectory = "/home/zanoni/arr-stack";
    qbittorrentPasswordSecretFile = "/run/agenix/arr-qbittorrent-password";
    samaritanoApiKeySecretFile = "/run/agenix/arr-samaritano-indexer-apikey";
  };

  provisionerDisabled = evalProvisioner (baseSettings // { enable = false; });
  provisionerEnabled = evalProvisioner baseSettings;
  enabledService = provisionerEnabled.systemd.services.arr-config-provisioner;
  enabledEnvironment = enabledService.environment;
in
{
  chise-arr-provisioner-disabled-defines-no-service =
    mkEvalCheck "chise-arr-provisioner-disabled-defines-no-service"
      (!(provisionerDisabled.systemd.services or { } ? arr-config-provisioner))
      "a host that does not opt in must get no provisioner service, so an unopted host never rewrites arr app config";

  chise-arr-provisioner-is-oneshot-running-packaged-engine =
    mkEvalCheck "chise-arr-provisioner-is-oneshot-running-packaged-engine"
      (
        enabledService.serviceConfig.Type == "oneshot"
        && lib.hasInfix "arr_config_provisioner" enabledService.serviceConfig.ExecStart
        && builtins.elem "multi-user.target" enabledService.wantedBy
      )
      "the provisioner must be a oneshot launching the packaged engine and wanted by multi-user.target so it reconciles the desired state once per activation";

  chise-arr-provisioner-reads-desired-state-and-runtime-config =
    mkEvalCheck "chise-arr-provisioner-reads-desired-state-and-runtime-config"
      (
        lib.hasInfix "desired-state" enabledEnvironment.ARR_PROVISIONER_DESIRED_STATE_DIR
        && lib.hasInfix "arr-stack/config" enabledEnvironment.ARR_PROVISIONER_CONFIG_ROOT
        && enabledEnvironment.ARR_BIND_ADDRESS_KEY == "ARR_BIND_ADDR"
      )
      "the provisioner must read the committed desired state, each app's on-disk api key under the config root, and the tailnet bind address from the .env key at runtime, so the tailscale IP stays out of the nix source";

  chise-arr-provisioner-injects-secrets-from-agenix =
    mkEvalCheck "chise-arr-provisioner-injects-secrets-from-agenix"
      (
        lib.hasInfix "agenix" enabledEnvironment.ARR_PROVISIONER_QBITTORRENT_PASSWORD_FILE
        && lib.hasInfix "agenix" enabledEnvironment.ARR_PROVISIONER_SAMARITANO_APIKEY_FILE
      )
      "the qBittorrent password and the private indexer key must reach the provisioner as agenix file paths substituted into placeholders at runtime, so no real secret is ever committed in the desired-state JSON";
}
