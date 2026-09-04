{
  config,
  lib,
  pkgs,
  ...
}:
let
  containerName = "stremio-streaming-server";
  image = "stremio/server:v4.21.1@sha256:3dc145603defba397467b2a2aa2354be2da1f86585d4ab825a70bd72782f2ef4";
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
  stateDirectory = "/var/lib/stremio-streaming-server";
  streamCacheDirectory = config.custom.stremioStreamingServer.streamCacheDirectory;
in
{
  options.custom.stremioStreamingServer.streamCacheDirectory = lib.mkOption {
    type = lib.types.str;
    default = "${stateDirectory}/stremio-cache";
    description = ''
      Host directory that holds the server's torrent stream cache, the only
      media the streaming server writes. Point it at the media drive to keep
      streamed media off the root disk; the unit requires that path's mount
      before it starts, so an absent drive keeps the server down rather than
      filling the root disk.
    '';
  };

  config.systemd.services.stremio-streaming-server = {
    description = "Private Stremio torrent streaming server";
    after = [
      "docker.service"
      "network-online.target"
      "tailscaled.service"
    ];
    wants = [ "network-online.target" ];
    requires = [ "docker.service" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.RequiresMountsFor = [ streamCacheDirectory ];

    serviceConfig = {
      ExecStartPre = [ "-${pkgs.docker}/bin/docker rm --force ${containerName}" ];
      ExecStart = lib.concatStringsSep " " [
        "${pkgs.docker}/bin/docker run"
        "--rm"
        "--name ${containerName}"
        "--cgroup-parent media-containers.slice"
        "--memory 512m"
        "--dns 1.1.1.1"
        "--dns 8.8.8.8"
        ''--health-cmd "curl -fsS http://127.0.0.1:11470/"''
        "--health-interval 30s"
        "--health-timeout 5s"
        "--health-start-period 60s"
        "--health-retries 3"
        "--env NO_CORS=1"
        "--env CASTING_DISABLED=1"
        "--publish ${tailnetBindAddress}:11470:11470"
        "--volume ${stateDirectory}:/root/.stremio-server"
        "--volume ${streamCacheDirectory}:/root/.stremio-server/stremio-cache"
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
