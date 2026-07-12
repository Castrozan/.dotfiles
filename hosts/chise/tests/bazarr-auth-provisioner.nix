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
        ../../../nixos/modules/bazarr-auth-provisioner
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.bazarrAuthProvisioner = settings;
        }
      ];
    }).config;

  baseSettings = {
    enable = true;
    configFile = "/home/zanoni/arr-stack/config/bazarr/config/config.yaml";
    containerName = "arr-bazarr";
    loginUsername = "lucas";
    passwordSecretFile = "/run/agenix/arr-bazarr-password";
  };

  provisionerDisabled = evalProvisioner (baseSettings // { enable = false; });
  provisionerEnabled = evalProvisioner baseSettings;
  enabledService = provisionerEnabled.systemd.services.bazarr-auth-provisioner;
  enabledEnvironment = enabledService.environment;
in
{
  chise-bazarr-auth-disabled-defines-no-service =
    mkEvalCheck "chise-bazarr-auth-disabled-defines-no-service"
      (!(provisionerDisabled.systemd.services or { } ? bazarr-auth-provisioner))
      "a host that does not opt in must get no bazarr-auth service, so an unopted host never rewrites bazarr's config";

  chise-bazarr-auth-is-oneshot-with-docker-on-path =
    mkEvalCheck "chise-bazarr-auth-is-oneshot-with-docker-on-path"
      (
        enabledService.serviceConfig.Type == "oneshot"
        && lib.hasInfix "bazarr_auth_provisioner" enabledService.serviceConfig.ExecStart
        && builtins.elem "multi-user.target" enabledService.wantedBy
        && builtins.elem pkgs.docker enabledService.path
      )
      "the provisioner must be a oneshot launching the packaged engine, wanted by multi-user.target, with the docker cli on its path so it can bounce the container only when already running";

  chise-bazarr-auth-injects-agenix-password-and-login =
    mkEvalCheck "chise-bazarr-auth-injects-agenix-password-and-login"
      (
        lib.hasInfix "agenix" enabledEnvironment.BAZARR_AUTH_PASSWORD_FILE
        && enabledEnvironment.BAZARR_AUTH_LOGIN_USERNAME == "lucas"
        && lib.hasInfix "config.yaml" enabledEnvironment.BAZARR_AUTH_CONFIG_FILE
        && enabledEnvironment.BAZARR_AUTH_CONTAINER_NAME == "arr-bazarr"
      )
      "the bazarr login password must reach the provisioner as an agenix file path, with the owner username and the config.yaml path passed at runtime so no secret is committed and the tailnet-only file is patched in place";
}
