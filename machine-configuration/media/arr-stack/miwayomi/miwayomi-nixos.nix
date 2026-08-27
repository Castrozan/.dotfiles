{
  config,
  lib,
  pkgs,
  ...
}:
let
  miwayomiConfig = config.custom.miwayomi;
  inherit (miwayomiConfig) stackHomeDirectory;
  extensionRepositoriesPackageDirectory = ../../manga-streaming/extension-repositories/scripts/suwayomi_extension_repositories;
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

    composePredecessorUnits = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Existing Compose applicator units that must settle before Miwayomi applies the same project.";
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
        ]
        ++ miwayomiConfig.composePredecessorUnits;
        requires = [
          "docker.service"
          "home-manager-zanoni.service"
        ]
        ++ miwayomiConfig.composePredecessorUnits;
        wants = [ "network-online.target" ];
        wantedBy = [ "multi-user.target" ];
        restartTriggers = [
          ../stack/docker-compose.yml
          ../stack/miwayomi-gateway.conf
          ../stack/miwayomi.Dockerfile
          ../stack/miwayomi-manga-input-initialization.patch
        ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = "${pkgs.docker-compose}/bin/docker-compose --file ${stackHomeDirectory}/docker-compose.yml --env-file ${stackHomeDirectory}/.env --project-directory ${stackHomeDirectory} --project-name arr-stack up --detach --build miwayomi flaresolverr miwayomi-gateway";
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
          ExecStart = "${pkgs.python3}/bin/python3 ${extensionRepositoriesPackageDirectory} miwayomi";
          TimeoutStartSec = "150s";
        };
      };
    };
  };
}
