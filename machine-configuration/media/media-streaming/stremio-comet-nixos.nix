{
  config,
  lib,
  pkgs,
  ...
}:
let
  containerName = "stremio-comet";
  image = "g0ldyy/comet@sha256:dca62133336e02784d02aaad861381820674d1c8e3e98a03797610b81ee4defe";
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
  port = "43214";
  runtimeEnvironmentFile = "/run/stremio-comet/prowlarr.env";
  prowlarrConfigFile = "${config.users.users.zanoni.home}/arr-stack/config/prowlarr/config.xml";
  environmentWriter = ./scripts/stremio_comet_environment.py;
in
{
  systemd.services.stremio-comet = {
    description = "Private Comet Stremio stream addon";
    after = [
      "docker.service"
      "network-online.target"
      "tailscaled.service"
    ];
    wants = [ "network-online.target" ];
    requires = [ "docker.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      ExecStartPre = [
        "-${pkgs.docker}/bin/docker rm --force ${containerName}"
        "${pkgs.python3}/bin/python3 ${environmentWriter} ${prowlarrConfigFile} ${runtimeEnvironmentFile}"
      ];
      ExecStart = lib.concatStringsSep " " [
        "${pkgs.docker}/bin/docker run"
        "--rm"
        "--init"
        "--name ${containerName}"
        "--network host"
        "--dns 127.0.0.53"
        "--read-only"
        "--cap-drop ALL"
        "--security-opt no-new-privileges:true"
        "--memory 1g"
        "--memory-swap 1g"
        "--cpus 2"
        "--pids-limit 256"
        "--health-cmd \"python -c \\\"import urllib.request; urllib.request.urlopen('http://${tailnetBindAddress}:${port}/health', timeout=5)\\\"\""
        "--health-interval 30s"
        "--health-timeout 5s"
        "--health-start-period 90s"
        "--health-retries 3"
        "--tmpfs /tmp:size=64m,mode=1777"
        "--volume /var/lib/stremio-comet:/app/data"
        "--env-file ${runtimeEnvironmentFile}"
        "--env DATABASE_TYPE=sqlite"
        "--env DATABASE_PATH=data/comet.db"
        "--env DATABASE_STARTUP_CLEANUP_INTERVAL=86400"
        "--env FASTAPI_HOST=${tailnetBindAddress}"
        "--env FASTAPI_PORT=${port}"
        "--env FASTAPI_WORKERS=1"
        "--env EXECUTOR_MAX_WORKERS=1"
        "--env PUBLIC_BASE_URL=https://stream.lucaszanoni.com/comet"
        "--env SCRAPE_PROWLARR=live"
        "--env PROWLARR_URL=http://${tailnetBindAddress}:9696"
        "--env 'PROWLARR_INDEXERS=[]'"
        "--env SCRAPE_NYAA=live"
        "--env NYAA_MAX_CONCURRENT_PAGES=2"
        "--env SCRAPE_ANIMETOSHO=live"
        "--env ANIMETOSHO_MAX_CONCURRENT_PAGES=3"
        "--env SCRAPE_SEADEX=live"
        "--env LIVE_SCRAPE_TIMEOUT=25"
        "--env INDEXER_MANAGER_TIMEOUT=15"
        "--env INDEXER_MANAGER_WAIT_TIMEOUT=10"
        "--env GET_TORRENT_TIMEOUT=10"
        "--env BACKGROUND_SCRAPER_ENABLED=False"
        "--env REMOVE_ADULT_CONTENT=True"
        image
      ];
      ExecStop = "-${pkgs.docker}/bin/docker stop --time 20 ${containerName}";
      Restart = "always";
      RestartSec = "5s";
      RuntimeDirectory = "stremio-comet";
      RuntimeDirectoryMode = "0700";
      StateDirectory = "stremio-comet";
      StateDirectoryMode = "0700";
      TimeoutStartSec = 0;
      TimeoutStopSec = "30s";
    };
  };
}
