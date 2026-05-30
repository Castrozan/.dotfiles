{
  homeDir,
  nixSystemPaths,
  crossPlatformMcpBridgeServiceSpecs,
  linuxOnlyMcpBridgeServiceSpecs,
}:
{
  pkgs,
  lib,
  healthCheckLib,
  ...
}:
let
  inherit (pkgs.stdenv.hostPlatform) isDarwin isLinux;

  allSpecs =
    crossPlatformMcpBridgeServiceSpecs // (lib.optionalAttrs isLinux linuxOnlyMcpBridgeServiceSpecs);

  mkMcpBridgeProbe =
    name: _spec:
    if isDarwin then
      healthCheckLib.mkLaunchdProbe {
        name = "mcp bridge: ${name}";
        label = "com.dotfiles.${name}";
      }
    else
      healthCheckLib.mkSystemdUserUnitProbe {
        name = "mcp bridge: ${name}";
        unit = "${name}.service";
      };

  mkSystemdUserUnitFromMcpBridgeServiceSpec =
    {
      description,
      launcher,
      linuxOnlyServiceExtraConfig,
    }:
    {
      Unit = {
        Description = description;
        After = [ "graphical-session.target" ];
      };
      Service = {
        Type = "simple";
        ExecStart = "${launcher}";
        Restart = "always";
        RestartSec = "3s";
        Environment = [
          "PATH=${nixSystemPaths}"
          "HOME=${homeDir}"
        ];
      }
      // linuxOnlyServiceExtraConfig;
      Install = {
        WantedBy = [ "default.target" ];
      };
    };

  mkLaunchdAgentFromMcpBridgeServiceSpec =
    name:
    {
      launcher,
      ...
    }:
    {
      enable = true;
      config = {
        Label = "com.dotfiles.${name}";
        ProgramArguments = [
          "${pkgs.bash}/bin/bash"
          "${launcher}"
        ];
        KeepAlive = true;
        RunAtLoad = true;
        StandardOutPath = "/tmp/${name}.log";
        StandardErrorPath = "/tmp/${name}.log";
        EnvironmentVariables = {
          PATH = nixSystemPaths;
          HOME = homeDir;
        };
      };
    };
in
{
  systemd.user.services = lib.mkIf isLinux (
    lib.mapAttrs (_: mkSystemdUserUnitFromMcpBridgeServiceSpec) (
      crossPlatformMcpBridgeServiceSpecs // linuxOnlyMcpBridgeServiceSpecs
    )
  );

  launchd.agents = lib.mkIf isDarwin (
    lib.mapAttrs mkLaunchdAgentFromMcpBridgeServiceSpec crossPlatformMcpBridgeServiceSpecs
  );

  healthCheck.probes = lib.mapAttrsToList mkMcpBridgeProbe allSpecs;
}
