{
  config,
  lib,
  pkgs,
  ...
}:
let
  brazilianMiddayHour = 12;

  exporterPython = pkgs.python312.withPackages (packages: [
    packages.python-gitlab
    packages.svgwrite
  ]);

  stateDirectory = "${config.home.homeDirectory}/.local/state/gitlab-contribution-heatmap-refresh";

  gitlab-contribution-heatmap-refresh = pkgs.writeShellScriptBin "gitlab-contribution-heatmap-refresh" ''
    export PATH="${
      lib.makeBinPath [
        pkgs.git
        pkgs.nodejs_22
        pkgs.gh
      ]
    }:$PATH"
    exec ${exporterPython}/bin/python3 ${./scripts/refresh_gitlab_contribution_heatmap.py} \
      --gitlab-url ${lib.escapeShellArg "https://${config.glab.gitlabHost}"} \
      --gitlab-token-file ${lib.escapeShellArg "${config.home.homeDirectory}/.secrets/glab-token"} \
      --checkout ${lib.escapeShellArg "${stateDirectory}/exporter"} \
      "$@"
  '';

  refreshCommand = "${gitlab-contribution-heatmap-refresh}/bin/gitlab-contribution-heatmap-refresh";
in
{
  config = lib.mkIf (config.glab.gitlabHost != null) (
    lib.mkMerge [
      { home.packages = [ gitlab-contribution-heatmap-refresh ]; }

      (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
        launchd.agents.gitlab-contribution-heatmap-refresh = {
          enable = true;
          config = {
            Label = "com.dotfiles.gitlab-contribution-heatmap-refresh";
            ProgramArguments = [ refreshCommand ];
            RunAtLoad = false;
            StartCalendarInterval = [
              {
                Hour = brazilianMiddayHour;
                Minute = 0;
              }
            ];
            StandardOutPath = "${config.home.homeDirectory}/Library/Logs/gitlab-contribution-heatmap-refresh.log";
            StandardErrorPath = "${config.home.homeDirectory}/Library/Logs/gitlab-contribution-heatmap-refresh.log";
          };
        };
      })

      (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
        systemd.user.services.gitlab-contribution-heatmap-refresh = {
          Unit.Description = "Refresh the private GitLab contribution heatmap on the GitHub profile";
          Service = {
            Type = "oneshot";
            ExecStart = refreshCommand;
          };
        };
        systemd.user.timers.gitlab-contribution-heatmap-refresh = {
          Unit.Description = "Brazilian midday refresh of the GitLab contribution heatmap";
          Timer = {
            OnCalendar = "*-*-* ${toString brazilianMiddayHour}:00:00 America/Sao_Paulo";
            Persistent = true;
          };
          Install.WantedBy = [ "timers.target" ];
        };
      })
    ]
  );
}
