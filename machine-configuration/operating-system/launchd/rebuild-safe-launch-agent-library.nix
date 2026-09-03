{
  config,
  lib,
  pkgs,
}:
let
  preserveRunningLaunchAgent = pkgs.writeShellApplication {
    name = "preserve-running-launch-agent";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.diffutils
      pkgs.gnugrep
      pkgs.nix
    ];
    text = builtins.readFile ./scripts/preserve-running-launch-agent.sh;
  };
in
{
  mkRebuildSafeLaunchAgent =
    {
      name,
      label,
      package,
      executableName,
      programArguments ? [ ],
      serviceConfig,
    }:
    assert lib.assertMsg (
      !(serviceConfig ? Label) && !(serviceConfig ? Program) && !(serviceConfig ? ProgramArguments)
    ) "mkRebuildSafeLaunchAgent owns Label, Program, and ProgramArguments";
    let
      launcherName = "${name}-rebuild-safe-launcher";
      packageStoreDirectoryName = builtins.baseNameOf (toString package);
      runtimeRootDirectory = "${config.xdg.stateHome}/rebuild-safe-launch-agents/${name}";
      launcher = pkgs.writeShellApplication {
        name = launcherName;
        runtimeInputs = [
          pkgs.coreutils
          pkgs.findutils
          pkgs.nix
        ];
        text = ''
          runtime_root_directory=${lib.escapeShellArg runtimeRootDirectory}
          runtime_root_path="$runtime_root_directory/${packageStoreDirectoryName}"
          mkdir -p "$runtime_root_directory"
          nix-store --realise ${lib.escapeShellArg (toString package)} --add-root "$runtime_root_path" --indirect >/dev/null
          find "$runtime_root_directory" -type l ! -name ${lib.escapeShellArg packageStoreDirectoryName} -delete
          exec ${lib.escapeShellArg "${package}/bin/${executableName}"} "$@"
        '';
      };
      stableLauncherPath = "${config.home.profileDirectory}/bin/${launcherName}";
    in
    {
      home = {
        packages = [ launcher ];
        activation."preserveRunningLaunchAgent-${name}" =
          lib.hm.dag.entryBetween [ "setupLaunchAgents" ] [ "writeBoundary" ]
            ''
              run ${preserveRunningLaunchAgent}/bin/preserve-running-launch-agent \
                ${lib.escapeShellArg label} \
                "$newGenPath/LaunchAgents/${label}.plist" \
                ${lib.escapeShellArg "${config.home.homeDirectory}/Library/LaunchAgents/${label}.plist"} \
                ${lib.escapeShellArg runtimeRootDirectory}
            '';
      };

      launchd.agents.${name} = {
        enable = true;
        config = serviceConfig // {
          Label = label;
          ProgramArguments = [ stableLauncherPath ] ++ programArguments;
        };
      };
    };
}
