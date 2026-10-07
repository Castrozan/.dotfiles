{
  config,
  lib,
  pkgs,
  hostname,
  ...
}:
let
  directory = ./shorts-automation;
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
  pinchtab =
    import
      ../../../agent-harness/agent-instructions/skills/workstation/browser/install/pinchtab-package.nix
      {
        inherit pkgs;
      };
  browserConfiguration = pkgs.writeText "shorts-browser-config.json" (
    builtins.toJSON {
      configVersion = "0.8.0";
      server = {
        port = "9867";
        bind = "127.0.0.1";
        stateDir = "${config.home.homeDirectory}/.pinchtab";
      };
      instanceDefaults.mode = "headed";
      profiles = {
        baseDir = "${config.home.homeDirectory}/.pinchtab/profiles";
        defaultProfile = "default";
      };
      multiInstance = {
        strategy = "explicit";
        instancePortStart = 9868;
        instancePortEnd = 9968;
      };
      security = {
        allowEvaluate = true;
        allowScreencast = true;
        allowDownload = true;
        allowUpload = true;
        uploadMaxRequestBytes = 104857600;
        uploadMaxFileBytes = 26214400;
        uploadMaxTotalBytes = 104857600;
      };
      autoSolver.enabled = false;
    }
  );
  browser = pkgs.writeShellScriptBin "shorts-browser" ''
    export SHORTS_PINCHTAB=${pinchtab}/bin/pinchtab
    export SHORTS_CONFIGURATION=${configuration}
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_browser.py "$@"
  '';
  browserServer = pkgs.writeShellScript "shorts-browser-server" ''
    export SHORTS_PINCHTAB=${pinchtab}/bin/pinchtab
    export SHORTS_BROWSER_CONFIGURATION=${browserConfiguration}
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_browser_server.py
  '';
  browserReady = pkgs.writeShellScript "shorts-browser-ready" ''
    export SHORTS_PINCHTAB=${pinchtab}/bin/pinchtab
    export SHORTS_CONFIGURATION=${configuration}
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_browser_start.py
  '';
  production = pkgs.writeShellScriptBin "shorts-production" ''
    export PATH=${
      lib.makeBinPath [
        pkgs.ffmpeg
        pkgs.yt-dlp
        pkgs.git
        pkgs.bash
      ]
    }:"${config.home.profileDirectory}/bin:$PATH"
    export SHORTS_CODEX=${config.codex.unwrappedPackage}/bin/codex
    export SHORTS_PINCHTAB=${pinchtab}/bin/pinchtab
    export SHORTS_GOAL_PROMPT=${directory}/goal.txt
    export SHORTS_CONFIGURATION=${configuration}
    export SHORTS_RUNBOOK=${directory}/RUNBOOK.md
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_production.py "$@"
  '';
in
{
  home.packages = [
    production
    browser
  ];
  systemd.user = lib.mkIf (pkgs.stdenv.isLinux && hostname == "chise") {
    services.shorts-browser = {
      Unit = {
        Description = "Persistent headed browser for the authorized Shorts profile";
        After = [ "graphical-session-pre.target" ];
        PartOf = [ "graphical-session.target" ];
      };
      Service = {
        ExecStart = browserServer;
        ExecStartPost = browserReady;
        TimeoutStartSec = 60;
        Restart = "on-failure";
        RestartSec = 5;
        KillMode = "control-group";
      };
      Install.WantedBy = [ "graphical-session.target" ];
    };
    services.shorts-production = {
      Unit = {
        Description = "Research, direct, verify and publish one original YouTube Short";
        Wants = [ "shorts-browser.service" ];
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
