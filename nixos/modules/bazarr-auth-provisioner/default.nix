{
  config,
  lib,
  pkgs,
  ...
}:
let
  bazarrAuthProvisionerConfig = config.custom.bazarrAuthProvisioner;
  provisionerPackageDirectory = ./scripts/bazarr_auth_provisioner;
in
{
  options.custom.bazarrAuthProvisioner = {
    enable = lib.mkEnableOption "a root systemd oneshot that gives bazarr a declarative owner web-UI login by md5-hashing an agenix password into the auth block of its config.yaml (type form, the given username), so a wiped config directory rebuilds the login from the repo. Bazarr is not a Servarr app and exposes no host-config API, so unlike radarr/sonarr/prowlarr its login is provisioned by patching config.yaml while the container is stopped rather than over HTTP; the container is bounced only when already running so the on-demand download chain is never forced up";

    configFile = lib.mkOption {
      type = lib.types.str;
      description = "Absolute host path to bazarr's bind-mounted config.yaml, whose auth block is patched in place; it persists on the host independently of the container so the login is set even while bazarr is down.";
    };

    containerName = lib.mkOption {
      type = lib.types.str;
      default = "arr-bazarr";
      description = "Docker container name for bazarr; stopped before the patch and restarted after, but only when it was already running, because bazarr holds one in-memory config copy with no file watcher and would otherwise both ignore a live edit and clobber it on its next write.";
    };

    loginUsername = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Web-UI login username written to bazarr's auth block; when empty the provisioner is a no-op so a missing value never enables auth with an empty user.";
    };

    passwordSecretFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the agenix-decrypted bazarr web-UI password, md5-hashed into auth.password; when unset or absent the auth block is left untouched rather than set to an empty password.";
    };

    configFileOwner = lib.mkOption {
      type = lib.types.str;
      default = "1000:100";
      description = "uid:gid the rewritten config.yaml is chowned back to (bazarr's PUID:PGID) so the container can still rewrite its own config on the next start; a root-owned config.yaml would block bazarr's own writes.";
    };
  };

  config = lib.mkIf bazarrAuthProvisionerConfig.enable {
    systemd.services.bazarr-auth-provisioner = {
      description = "Set bazarr's owner web-UI login declaratively from an agenix secret";
      after = [ "docker.service" ];
      wants = [ "docker.service" ];
      wantedBy = [ "multi-user.target" ];
      path = [ pkgs.docker ];
      environment = {
        BAZARR_AUTH_CONFIG_FILE = bazarrAuthProvisionerConfig.configFile;
        BAZARR_AUTH_CONTAINER_NAME = bazarrAuthProvisionerConfig.containerName;
        BAZARR_AUTH_LOGIN_USERNAME = bazarrAuthProvisionerConfig.loginUsername;
        BAZARR_AUTH_PASSWORD_FILE = bazarrAuthProvisionerConfig.passwordSecretFile;
        BAZARR_AUTH_FILE_OWNER = bazarrAuthProvisionerConfig.configFileOwner;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${provisionerPackageDirectory}";
      };
    };
  };
}
