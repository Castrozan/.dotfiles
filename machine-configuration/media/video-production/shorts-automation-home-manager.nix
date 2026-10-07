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
      paid_image_generation = false;
      provider_overage = false;
    }
  );
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
    export SHORTS_GOAL_PROMPT=${directory}/goal.txt
    export SHORTS_CONFIGURATION=${configuration}
    export SHORTS_RUNBOOK=${directory}/RUNBOOK.md
    exec ${pkgs.python312}/bin/python3 ${directory}/scripts/shorts_production.py "$@"
  '';
in
{
  home.packages = [ production ];
  systemd.user = lib.mkIf (pkgs.stdenv.isLinux && hostname == "chise") {
    services.shorts-production = {
      Unit.Description = "Research, direct, verify and publish one original YouTube Short";
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
