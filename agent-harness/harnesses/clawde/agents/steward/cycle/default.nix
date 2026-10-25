{
  lib,
  pkgs,
  hostname,
  config,
  ...
}:
let
  inherit (config.home) homeDirectory;
  agentDirectory = "${homeDirectory}/clawde/steward";
  idleMarkerName = "steward-operator-idle";
  operatorIdleSeconds = 900;
  removeIdleMarker = "${pkgs.coreutils}/bin/rm -f %t/${idleMarkerName}";

  forgePackages =
    (import ../../../../../agent-instructions/skills/development/forge/install { inherit pkgs; })
    .packages;
  rebuild =
    import ../../../../../../machine-configuration/development/system-rebuild/scripts/rebuild
      {
        inherit pkgs hostname;
      };

  settings = pkgs.writeText "steward-cycle-settings.json" (
    builtins.toJSON {
      repository = "${homeDirectory}/.dotfiles";
      entrypoint = "${homeDirectory}/zanoni-system";
      configuration_attribute = "nixosConfigurations.${hostname}.config.system.build.toplevel";
      state_directory = "${agentDirectory}/state/cycle";
      idle_marker_name = idleMarkerName;
      inbox_directory = "${agentDirectory}/inbox";
      peers_file = "${agentDirectory}/peers.json";
      nix_binary = "/run/current-system/sw/bin/nix";
      rebuild_command = "${rebuild}/bin/rebuild";
    }
  );

  source = pkgs.runCommand "steward-cycle-source" { } ''
    mkdir -p $out
    cp ${./scripts}/*.py $out/
    cp ${../continuous_integration_status.py} $out/continuous_integration_status.py
    cd $out && ${pkgs.python312}/bin/python3 -B -c "import steward_cycle"
  '';

  stewardCycle = pkgs.writeShellScriptBin "steward-cycle" ''
    export PATH="${
      lib.makeBinPath (
        [
          pkgs.git
          pkgs.openssh
          pkgs.systemd
          pkgs.coreutils
          pkgs.gh
        ]
        ++ forgePackages
      )
    }:/run/wrappers/bin''${PATH:+:$PATH}"
    export STEWARD_CYCLE_SETTINGS=${settings}
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
  config = lib.mkIf (hostname == "chise") {
    home.packages = [ stewardCycle ];

    systemd.user.services.steward-operator-idle-marker = {
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
  };
}
