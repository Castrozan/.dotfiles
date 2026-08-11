{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config.home) homeDirectory;
  seanimePackage = import ./seanime-package.nix { inherit pkgs; };
  seanimeDataDirectory = "${homeDirectory}/.local/share/seanime";
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
  seanimeUrl = "http://${tailnetBindAddress}:43211";
  provisionerPackageDirectory = ./scripts/seanime_provisioner;
  providerPayload = builtins.readFile ./prowlarr-anime-torrent-provider.js;
  providerManifest = builtins.toJSON {
    id = "prowlarr-torrent-provider";
    name = "Prowlarr Torrent Provider";
    version = "1.0.0";
    manifestURI = "";
    language = "javascript";
    type = "anime-torrent-provider";
    description = "Search the private Prowlarr instance and resolve only the selected torrent for streaming.";
    author = "Lucas Zanoni";
    icon = "";
    website = "https://prowlarr.com";
    readme = "";
    lang = "multi";
    payload = providerPayload;
    payloadURI = "";
    userConfig = {
      requiresConfig = true;
      version = 1;
      fields = [
        {
          name = "prowlarrBaseUrl";
          label = "Prowlarr base URL";
          type = "text";
          default = "http://127.0.0.1:9696";
        }
        {
          name = "prowlarrApiKey";
          label = "Prowlarr API key";
          type = "text";
          default = "";
        }
        {
          name = "resultLimit";
          label = "Maximum results";
          type = "text";
          default = "50";
        }
      ];
    };
  };
in
{
  home.packages = [ seanimePackage ];

  home.file.".local/share/seanime/extensions/prowlarr-torrent-provider.json".text = providerManifest;

  systemd.user = {
    services = {
      seanime = {
        Unit = {
          Description = "Seanime private anime streaming server";
          After = [ "network.target" ];
          StartLimitIntervalSec = 0;
        };

        Service = {
          ExecStart = "${seanimePackage}/bin/seanime --datadir=${seanimeDataDirectory} --host=${tailnetBindAddress} --port=43211 --disable-password";
          Restart = "on-failure";
          RestartSec = "5s";
          WorkingDirectory = homeDirectory;
          RuntimeDirectory = "seanime";
          RuntimeDirectoryMode = "0700";
          Environment = [
            "HOME=${homeDirectory}"
            "TMPDIR=%t/seanime"
            "PATH=${
              lib.makeBinPath [
                pkgs.ffmpeg
                pkgs.mpv
              ]
            }"
          ];
        };

        Install.WantedBy = [ "default.target" ];
      };

      seanime-provisioner = {
        Unit = {
          Description = "Reconcile Seanime streaming and Prowlarr settings";
          After = [ "seanime.service" ];
          Requires = [ "seanime.service" ];
          StartLimitIntervalSec = 0;
        };

        Service = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = "${pkgs.python3}/bin/python3 ${provisionerPackageDirectory}";
          TimeoutStartSec = "90s";
          Restart = "on-failure";
          RestartSec = "10s";
          Environment = [
            "SEANIME_URL=${seanimeUrl}"
            "SEANIME_TAILNET_ADDRESS=${tailnetBindAddress}"
            "SEANIME_PROWLARR_CONFIG_FILE=${homeDirectory}/arr-stack/config/prowlarr/config.xml"
            "SEANIME_MPV_PATH=${pkgs.mpv}/bin/mpv"
          ];
        };

        Install.WantedBy = [ "default.target" ];
      };
    };

    startServices = "sd-switch";
  };
}
