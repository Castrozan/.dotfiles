{
  config,
  lib,
  pkgs,
  latest,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  arrStackDataRoot = "${homeDir}/arr-stack/data";
  mangaDownloadRoot = "${arrStackDataRoot}/manga";
  chiseTailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
  suwayomiServerPackage = import ./suwayomi-server-release-ahead-of-nixpkgs.nix { inherit latest; };
  kcefChromiumLibraryPath = import ./runtime-downloaded-kcef-chromium-library-path.nix {
    inherit pkgs;
  };
  forcedServerSettings = {
    ip = chiseTailnetBindAddress;
    downloadAsCbz = "true";
    downloadsPath = mangaDownloadRoot;
    systemTrayEnabled = "false";
    webUIChannel = "bundled";
    webUIUpdateCheckInterval = "0";
  };
  forcedServerSettingsJvmArguments = lib.concatStringsSep " " (
    lib.mapAttrsToList (
      settingName: settingValue: "-Dsuwayomi.tachidesk.config.server.${settingName}=${settingValue}"
    ) forcedServerSettings
  );
in
{
  imports = [
    ./extension-repositories/suwayomi-extension-repositories-home-manager.nix
  ];

  systemd.user.services.suwayomi-server = {
    Unit = {
      Description = "Suwayomi-Server - Manga server";
      After = [ "network.target" ];
      ConditionPathIsMountPoint = arrStackDataRoot;
      StartLimitIntervalSec = 0;
    };

    Service = {
      ExecStart = "${suwayomiServerPackage}/bin/tachidesk-server";
      Restart = "always";
      RestartSec = "5s";
      WorkingDirectory = homeDir;
      Environment = [
        "HOME=${homeDir}"
        "TACHIDESK_DATA_DIR=${homeDir}/.local/share/Tachidesk"
        "LD_LIBRARY_PATH=${kcefChromiumLibraryPath}"
        ''"JAVA_TOOL_OPTIONS=${forcedServerSettingsJvmArguments}"''
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  systemd.user.startServices = "sd-switch";
}
