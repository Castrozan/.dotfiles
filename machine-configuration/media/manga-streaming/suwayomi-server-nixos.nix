{
  config,
  lib,
  pkgs,
  ...
}:
let
  homeDirectory = config.users.users.zanoni.home;
  arrStackDataRoot = "${homeDirectory}/arr-stack/data";
  mangaDownloadRoot = "${arrStackDataRoot}/manga";
  dataDirectory = "${homeDirectory}/.local/share/Tachidesk";
  containerDataDirectory = "/home/suwayomi/.local/share/Tachidesk";
  containerName = "suwayomi-server";
  image = "ghcr.io/suwayomi/suwayomi-server:v2.3.2243-preview@sha256:2b95476844614748285ecba0deef97cb8eabd17c6ccb58d136f829ec20b8040f";
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
in
{
  imports = [ ./extension-repositories/suwayomi-extension-repositories-nixos.nix ];

  systemd = {
    services.suwayomi-server = {
      description = "Private Suwayomi manga server";
      after = [
        "docker.service"
        "home-manager-zanoni.service"
        "network-online.target"
        "tailscaled.service"
      ];
      requires = [
        "docker.service"
        "home-manager-zanoni.service"
      ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      unitConfig = {
        RequiresMountsFor = [ arrStackDataRoot ];
        StartLimitIntervalSec = 0;
      };
      serviceConfig = {
        ExecStartPre = [ "-${pkgs.docker}/bin/docker rm --force ${containerName}" ];
        ExecStart = lib.concatStringsSep " " [
          "${pkgs.docker}/bin/docker run"
          "--rm"
          "--name ${containerName}"
          "--user 1000:100"
          "--security-opt no-new-privileges:true"
          "--cgroup-parent media-containers.slice"
          "--memory 3g"
          "--dns 1.1.1.1"
          "--dns 8.8.8.8"
          "--publish ${tailnetBindAddress}:4567:4567"
          "--health-cmd \"curl -fsS http://127.0.0.1:4567/api/v1/health\""
          "--health-interval 30s"
          "--health-timeout 5s"
          "--health-start-period 120s"
          "--health-retries 3"
          "--volume ${mangaDownloadRoot}:${containerDataDirectory}/downloads"
          "--volume ${dataDirectory}:${containerDataDirectory}"
          "--env TZ=America/Sao_Paulo"
          "--env BIND_IP=0.0.0.0"
          "--env BIND_PORT=4567"
          "--env DOWNLOAD_AS_CBZ=true"
          "--env WEB_UI_CHANNEL=bundled"
          "--env WEB_UI_UPDATE_INTERVAL=0"
          "--env KCEF_ENABLED=true"
          ''--env "JAVA_TOOL_OPTIONS=-Xms128m -Xmx768m"''
          image
        ];
        ExecStop = "-${pkgs.docker}/bin/docker stop --time 20 ${containerName}";
        Restart = "always";
        RestartSec = "5s";
        TimeoutStartSec = 0;
        TimeoutStopSec = "30s";
      };
    };

    tmpfiles.rules = [
      "d ${dataDirectory} 0755 zanoni users - -"
      "d ${mangaDownloadRoot} 0755 zanoni users - -"
    ];
  };
}
