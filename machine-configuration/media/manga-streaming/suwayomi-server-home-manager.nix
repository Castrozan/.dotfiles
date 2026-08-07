{
  config,
  lib,
  latest,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  arrStackDataRoot = "${homeDir}/arr-stack/data";
  mangaDownloadRoot = "${arrStackDataRoot}/manga";
  machineIdentityMapPath = ../../../private-configuration/machines.nix;
  privateConfigPresent = builtins.pathExists machineIdentityMapPath;
  chiseMachineIdentity = lib.optionalAttrs privateConfigPresent (import machineIdentityMapPath).chise;
  chiseTailnetBindAddress = chiseMachineIdentity.tailscaleIp or "127.0.0.1";
  forcedServerSettings = {
    ip = chiseTailnetBindAddress;
    downloadAsCbz = "true";
    downloadsPath = mangaDownloadRoot;
    systemTrayEnabled = "false";
  };
  forcedServerSettingsJvmArguments = lib.concatStringsSep " " (
    lib.mapAttrsToList (
      settingName: settingValue: "-Dsuwayomi.tachidesk.config.server.${settingName}=${settingValue}"
    ) forcedServerSettings
  );
in
{
  systemd.user.services.suwayomi-server = {
    Unit = {
      Description = "Suwayomi-Server - Manga server";
      After = [ "network.target" ];
      ConditionPathIsMountPoint = arrStackDataRoot;
      StartLimitIntervalSec = 0;
    };

    Service = {
      ExecStart = "${latest.suwayomi-server}/bin/tachidesk-server";
      Restart = "on-failure";
      RestartSec = "5s";
      WorkingDirectory = homeDir;
      Environment = [
        "HOME=${homeDir}"
        "TACHIDESK_DATA_DIR=${homeDir}/.local/share/Tachidesk"
        ''"JAVA_TOOL_OPTIONS=${forcedServerSettingsJvmArguments}"''
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  systemd.user.startServices = "sd-switch";
}
