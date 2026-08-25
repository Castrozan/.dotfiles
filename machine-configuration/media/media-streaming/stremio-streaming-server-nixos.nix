{ lib, pkgs, ... }:
let
  containerName = "stremio-streaming-server";
  image = "stremio/server:v4.21.1@sha256:3dc145603defba397467b2a2aa2354be2da1f86585d4ab825a70bd72782f2ef4";
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
in
{
  systemd.services.stremio-streaming-server = {
    description = "Private Stremio torrent streaming server";
    after = [
      "docker.service"
      "network-online.target"
      "tailscaled.service"
    ];
    wants = [ "network-online.target" ];
    requires = [ "docker.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      ExecStartPre = [ "-${pkgs.docker}/bin/docker rm --force ${containerName}" ];
      ExecStart = lib.concatStringsSep " " [
        "${pkgs.docker}/bin/docker run"
        "--rm"
        "--name ${containerName}"
        "--env NO_CORS=1"
        "--env CASTING_DISABLED=1"
        "--publish ${tailnetBindAddress}:11470:11470"
        "--volume /var/lib/stremio-streaming-server:/root/.stremio-server"
        image
      ];
      ExecStop = "-${pkgs.docker}/bin/docker stop --time 20 ${containerName}";
      Restart = "always";
      RestartSec = "5s";
      StateDirectory = "stremio-streaming-server";
      TimeoutStartSec = 0;
      TimeoutStopSec = "30s";
    };
  };
}
