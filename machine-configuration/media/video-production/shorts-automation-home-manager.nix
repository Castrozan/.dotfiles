{
  config,
  lib,
  pkgs,
  hostname,
  ...
}:
let
  directory = ./shorts-automation;
  speech = import ../media-generation/speech-package.nix { inherit pkgs; };
  configuration = pkgs.writeText "shorts-production-config.json" (
    builtins.toJSON {
      channel_id = "UC6Vso0wnLrqyf60Nn-rrpfw";
      channel_handle = "@realslimshady1375";
      timezone = "America/Sao_Paulo";
      hours = [
        9
        15
        21
      ];
      model = "gpt-6.1-sol";
      publisher = "youtube-studio";
      browser_profile = "shorts";
      browser_profile_id = "prof_474a744f";
      paid_image_generation = false;
      provider_overage = false;
    }
  );
  opencli =
    import ../../../agent-harness/agent-instructions/skills/workstation/browser/install/opencli-jobs.nix
      {
        inherit pkgs;
        nodejs = pkgs.nodejs_22;
        muteAudio = true;
      };
  browser = pkgs.writeShellScriptBin "shorts-browser" ''
    export SHORTS_OPENCLI=${opencli.command}/bin/opencli
    export SHORTS_CONFIGURATION=${configuration}
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_browser.py "$@"
  '';
  browserServer = pkgs.writeShellScript "shorts-browser-server" ''
    export SHORTS_OPENCLI=${opencli.command}/bin/opencli
    export SHORTS_CONFIGURATION=${configuration}
    exec ${opencli.runner}/bin/opencli-run --profile shorts --timeout 7800 -- ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_browser_server.py
  '';
  browserReady = pkgs.writeShellScript "shorts-browser-ready" ''
    export SHORTS_OPENCLI=${opencli.command}/bin/opencli
    export SHORTS_CONFIGURATION=${configuration}
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_browser_start.py
  '';
  production = pkgs.writeShellScriptBin "shorts-production" ''
    export PATH=${
      lib.makeBinPath (
        [
          browser
          speech
          pkgs.ffmpeg
          pkgs.yt-dlp
          pkgs.git
          pkgs.bash
        ]
        ++ lib.optionals pkgs.stdenv.isLinux [ pkgs.systemd ]
      )
    }:"${config.home.profileDirectory}/bin:$PATH"
    export SHORTS_CODEX=${config.codex.unwrappedPackage}/bin/codex
    export SHORTS_OPENCLI=${opencli.command}/bin/opencli
    export SHORTS_GOAL_PROMPT=${directory}/goal.txt
    export SHORTS_CONFIGURATION=${configuration}
    export SHORTS_RUNBOOK=${directory}/RUNBOOK.md
    export SHORTS_RECOVERY_GOAL=${directory}/recovery-goal.txt
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_production.py "$@"
  '';
in
{
  home.packages = [
    production
    browser
  ];
  home.activation.importOpencliShortsProfile = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    $DRY_RUN_CMD ${pkgs.python312}/bin/python3 ${../../../agent-harness/agent-instructions/skills/workstation/browser/install/scripts/opencli/import_opencli_profile.py} \
      ${lib.escapeShellArg "${config.home.homeDirectory}/.pinchtab/profiles/prof_474a744f"} \
      ${lib.escapeShellArg "${config.home.homeDirectory}/.local/share/opencli/profiles/shorts"}
  '';
  systemd.user = lib.mkIf (pkgs.stdenv.isLinux && hostname == "chise") {
    services = {
      shorts-browser = {
        Unit = {
          Description = "On-demand headless browser for the authorized Shorts profile";
          PartOf = [ "shorts-production.service" ];
          StopWhenUnneeded = true;
        };
        Service = {
          ExecStart = browserServer;
          ExecStartPost = browserReady;
          TimeoutStartSec = 90;
          TimeoutStopSec = 30;
          Restart = "on-failure";
          RestartSec = 5;
          KillMode = "control-group";
        };
      };
      shorts-production = {
        Unit = {
          Description = "Research, direct, verify and publish one original YouTube Short";
          Requires = [ "shorts-browser.service" ];
          After = [ "shorts-browser.service" ];
        };
        Service = {
          Type = "oneshot";
          ExecStart = "${production}/bin/shorts-production run";
          TimeoutStartSec = "125min";
          KillMode = "control-group";
          Nice = 10;
          WorkingDirectory = config.home.homeDirectory;
          Environment = [ "TZ=America/Sao_Paulo" ];
        };
      };
      shorts-recovery = {
        Unit = {
          Description = "Recover one explicitly queued held Short";
          Requires = [ "shorts-browser.service" ];
          After = [
            "shorts-browser.service"
            "shorts-production.service"
          ];
        };
        Service = {
          Type = "oneshot";
          ExecStart = "${production}/bin/shorts-production recover-next";
          TimeoutStartSec = "125min";
          KillMode = "control-group";
          Nice = 10;
          WorkingDirectory = config.home.homeDirectory;
          Environment = [ "TZ=America/Sao_Paulo" ];
        };
      };
    };
    timers.shorts-production = {
      Unit.Description = "Three daily Shorts production slots in Sao Paulo time";
      Timer = {
        OnCalendar = "*-*-* 09,15,21:00:00 America/Sao_Paulo";
        Persistent = false;
        AccuracySec = "1min";
        Unit = "shorts-production.service";
      };
      Install.WantedBy = [ "timers.target" ];
    };

  };
}
