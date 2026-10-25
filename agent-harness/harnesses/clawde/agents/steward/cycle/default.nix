{
  lib,
  pkgs,
  hostname,
  config,
  ...
}:
let
  inherit (config.home) homeDirectory;
  inherit (pkgs.stdenv.hostPlatform) isLinux isDarwin;
  agentDirectory = "${homeDirectory}/clawde/steward";
  settingsFile = "clawde/steward/cycle-settings.json";
  idleMarkerName = "steward-operator-idle";
  operatorIdleSeconds = 900;
  removeIdleMarker = "${pkgs.coreutils}/bin/rm -f %t/${idleMarkerName}";
  machineLocalEntrypointOwner = "chise";
  activatesDuringActiveUse = hostname == "rin";

  forgePackages =
    (import ../../../../../agent-instructions/skills/development/forge/install { inherit pkgs; })
    .packages;
  rebuild =
    import ../../../../../../machine-configuration/development/system-rebuild/scripts/rebuild
      {
        inherit pkgs hostname;
      };

  settings = {
    repository = "${homeDirectory}/.dotfiles";
    entrypoint =
      if hostname == machineLocalEntrypointOwner then "${homeDirectory}/zanoni-system" else null;
    configuration_attribute =
      if isDarwin then
        "darwinConfigurations.${hostname}.system"
      else
        "nixosConfigurations.${hostname}.config.system.build.toplevel";
    state_directory = "${agentDirectory}/state/cycle";
    idle_marker_name = if isLinux then idleMarkerName else null;
    operator_idle_required = !activatesDuringActiveUse;
    job_isolation = if isLinux then "systemd-scope" else "darwin-background";
    inbox_directory = "${agentDirectory}/inbox";
    peers_file = "${agentDirectory}/peers.json";
    nix_binary = "/run/current-system/sw/bin/nix";
    rebuild_command = "${rebuild}/bin/rebuild";
  };

  source = pkgs.runCommand "steward-cycle-source" { } ''
    mkdir -p $out
    cp ${./scripts}/*.py $out/
    cp ${../continuous_integration_status.py} $out/continuous_integration_status.py
    cd $out && ${pkgs.python312}/bin/python3 -B -c "import steward_cycle"
  '';

  stewardCycleTools = [
    pkgs.git
    pkgs.openssh
    pkgs.coreutils
    pkgs.gh
  ]
  ++ lib.optional isLinux pkgs.systemd
  ++ forgePackages;
  platformCommandDirectories = if isLinux then "/run/wrappers/bin" else "/usr/sbin:/usr/bin:/bin";

  stewardCycle = pkgs.writeShellScriptBin "steward-cycle" ''
    export PATH="${lib.makeBinPath stewardCycleTools}:${platformCommandDirectories}''${PATH:+:$PATH}"
    export STEWARD_CYCLE_SETTINGS=${lib.escapeShellArg "${homeDirectory}/${settingsFile}"}
    exec ${pkgs.python312}/bin/python3 ${source}/steward_cycle.py "$@"
  '';

  idleListenerConfiguration = pkgs.writeTextDir "hypr/hypridle.conf" ''
    general {
        ignore_dbus_inhibit = true
        inhibit_sleep = 0
    }

    listener {
        timeout = ${toString operatorIdleSeconds}
        on-timeout = ${pkgs.coreutils}/bin/touch "$XDG_RUNTIME_DIR/${idleMarkerName}"
        on-resume = ${pkgs.coreutils}/bin/rm -f "$XDG_RUNTIME_DIR/${idleMarkerName}"
    }
  '';
in
{
  home = {
    packages = [ stewardCycle ];
    file.${settingsFile}.text = builtins.toJSON settings;
  };

  systemd.user.services = lib.mkIf isLinux {
    steward-operator-idle-marker = {
      Unit.Description = "Operator idle marker that lets the steward cycle activate a validated system";
      Service = {
        Environment = "XDG_CONFIG_HOME=${idleListenerConfiguration}";
        ExecStartPre = removeIdleMarker;
        ExecStart = "${pkgs.hypridle}/bin/hypridle --quiet";
        ExecStopPost = removeIdleMarker;
        Restart = "always";
        RestartSec = 30;
      };
      Install.WantedBy = [ "default.target" ];
    };
  };

  clawde.agents.steward = {
    launchOnTrigger = true;
    launchGateIntervalSeconds = 300;
    heartbeatGateCommand = ''
      ${stewardCycle}/bin/steward-cycle run >/dev/null 2>&1
      clawde-heartbeat-change-gate --label steward --retries-while-pending 1 --probe ${lib.escapeShellArg "${stewardCycle}/bin/steward-cycle attention"}
    '';
    heartbeatPrompt = builtins.readFile ./run-once-prompt.md;
    personality = "\n" + builtins.readFile ./agent-instructions.md;
  };
}
