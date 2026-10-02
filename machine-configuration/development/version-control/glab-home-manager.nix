{
  config,
  lib,
  hostname,
  healthCheckLib,
  pkgs,
  ...
}:
let
  privateConfigRoot = ../../../private-configuration;
  privateGlabHostPath = "${toString privateConfigRoot}/machines/${hostname}/glab-host.nix";
  privateGlabHostExists = builtins.pathExists privateGlabHostPath;
in
{
  imports = lib.optionals privateGlabHostExists [
    privateGlabHostPath
  ];

  options.glab.gitlabHost = lib.mkOption {
    type = lib.types.nullOr lib.types.str;
    default = null;
    description = "Optional hosts.<host> entry for glab-cli. Set in private-configuration when the host is non-public.";
  };

  config =
    let
      glabConfigDir = "${config.home.homeDirectory}/.config/glab-cli";
      glabConfigFile = "${glabConfigDir}/config.yml";
      personalTokenFile = "${config.home.homeDirectory}/.secrets/gitlab-com-token";
      personalCredentialEnabled = config.age.secrets ? "credentials/gitlab-com-token";
      initialGlabConfig = pkgs.writeText "glab-configuration.json" (
        builtins.toJSON {
          git_protocol = "ssh";
          editor = "vim";
          browser = "";
          glamour_style = "dark";
          pager = "";
          check_update = false;
          no_prompt = false;
          hosts =
            lib.optionalAttrs (config.glab.gitlabHost != null) {
              ${config.glab.gitlabHost} = {
                api_host = config.glab.gitlabHost;
                git_protocol = "ssh";
                token_file = "${config.home.homeDirectory}/.secrets/glab-token";
              };
            }
            // lib.optionalAttrs personalCredentialEnabled {
              "gitlab.com" = {
                api_host = "gitlab.com";
                git_protocol = "https";
                token_file = personalTokenFile;
              };
            };
        }
      );
      personalGitCredentialHelper = pkgs.writeShellScript "gitlab-com-credential-helper" ''
        if [ "$1" = get ] && [ -s ${lib.escapeShellArg personalTokenFile} ]; then
          printf 'username=oauth2\n'
          printf 'password=%s\n' "$(cat ${lib.escapeShellArg personalTokenFile})"
        fi
      '';
    in
    {
      home.activation.setupGlabConfig = {
        after = [
          "writeBoundary"
          "disableAgenixLaunchdRestartLoop"
        ];
        before = [ ];
        data = ''
          ${pkgs.python312}/bin/python3 ${./scripts/write_glab_configuration.py} ${initialGlabConfig} ${lib.escapeShellArg glabConfigFile}
        '';
      };

      programs.git.settings.credential."https://gitlab.com" = lib.mkIf personalCredentialEnabled {
        helper = [
          ""
          "!${personalGitCredentialHelper}"
        ];
      };

      healthCheck.probes =
        map
          (
            gitlabHost:
            healthCheckLib.mkBinaryProbe {
              name = "glab config holds a token for ${gitlabHost}";
              command = "glab config get token --host ${gitlabHost} | grep -q .";
            }
          )
          (
            lib.optional (config.glab.gitlabHost != null) config.glab.gitlabHost
            ++ lib.optional personalCredentialEnabled "gitlab.com"
          );
    };
}
