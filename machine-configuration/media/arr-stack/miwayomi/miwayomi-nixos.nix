{
  config,
  lib,
  pkgs,
  ...
}:
let
  miwayomiConfig = config.custom.miwayomi;
  stackHomeDirectory = miwayomiConfig.stackHomeDirectory;
  repositoryProvisioner = pkgs.writeShellScript "miwayomi-extension-repositories" ''
    set -Eeuo pipefail
    ${pkgs.jq}/bin/jq -e 'type == "array" and length > 0 and all(.[]; type == "string" and length > 0)' "$MIWAYOMI_EXTENSION_REPOSITORIES_FILE" >/dev/null
    declared="$(${pkgs.jq}/bin/jq -c '{repos:.}' "$MIWAYOMI_EXTENSION_REPOSITORIES_FILE")"
    ${pkgs.curl}/bin/curl --fail --silent --show-error --connect-timeout 1 --max-time 2 --retry 60 --retry-delay 1 --retry-max-time 80 --retry-connrefused "$MIWAYOMI_BASE_URL/api/v1/health" >/dev/null
    current="$(${pkgs.curl}/bin/curl --fail --silent --show-error "$MIWAYOMI_BASE_URL/api/v1/extensions/repos")"
    [[ "$(printf '%s' "$current" | ${pkgs.jq}/bin/jq -Sc '.repos')" == "$(printf '%s' "$declared" | ${pkgs.jq}/bin/jq -Sc '.repos')" ]] || printf '%s' "$declared" | ${pkgs.curl}/bin/curl --fail --silent --show-error --request POST --header 'Content-Type: application/json' --data-binary @- "$MIWAYOMI_BASE_URL/api/v1/extensions/repos" >/dev/null
    written="$(${pkgs.curl}/bin/curl --fail --silent --show-error "$MIWAYOMI_BASE_URL/api/v1/extensions/repos")"
    [[ "$(printf '%s' "$written" | ${pkgs.jq}/bin/jq -Sc '.repos')" == "$(printf '%s' "$declared" | ${pkgs.jq}/bin/jq -Sc '.repos')" ]]
  '';
in
{
  options.custom.miwayomi = {
    enable = lib.mkEnableOption "Miwayomi and its FlareSolverr sidecar in the arr-stack Compose project";

    stackHomeDirectory = lib.mkOption {
      type = lib.types.str;
      description = "Absolute directory holding the arr-stack Compose declaration and environment file.";
    };

    baseUrl = lib.mkOption {
      type = lib.types.str;
      description = "Tailnet-only Miwayomi base URL used by the host repository provisioner.";
    };

    repositoryListSecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Agenix-decrypted JSON list of Miwayomi extension repository URLs.";
    };
  };

  config = lib.mkIf miwayomiConfig.enable {
    systemd.services = {
      miwayomi-compose = {
        description = "Apply Miwayomi and FlareSolverr in the arr-stack Compose project";
        after = [
          "docker.service"
          "home-manager-zanoni.service"
          "network-online.target"
        ];
        requires = [
          "docker.service"
          "home-manager-zanoni.service"
        ];
        wants = [ "network-online.target" ];
        wantedBy = [ "multi-user.target" ];
        restartTriggers = [ ../stack/docker-compose.yml ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = "${pkgs.docker-compose}/bin/docker-compose --file ${stackHomeDirectory}/docker-compose.yml --env-file ${stackHomeDirectory}/.env --project-directory ${stackHomeDirectory} --project-name arr-stack up --detach miwayomi flaresolverr";
        };
      };

      miwayomi-extension-repositories = {
        description = "Reconcile Miwayomi extension repositories";
        after = [ "miwayomi-compose.service" ];
        requires = [ "miwayomi-compose.service" ];
        wantedBy = [ "multi-user.target" ];
        environment = {
          MIWAYOMI_BASE_URL = miwayomiConfig.baseUrl;
          MIWAYOMI_EXTENSION_REPOSITORIES_FILE = miwayomiConfig.repositoryListSecretFile;
        };
        serviceConfig = {
          Type = "oneshot";
          ExecStart = repositoryProvisioner;
          TimeoutStartSec = "90s";
        };
      };
    };
  };
}
