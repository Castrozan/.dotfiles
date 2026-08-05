{
  config,
  lib,
  hostname,
  healthCheckLib,
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

      hostsSection =
        if config.glab.gitlabHost == null then
          ""
        else
          ''

            hosts:
              ${config.glab.gitlabHost}:
                api_host: ${config.glab.gitlabHost}
                git_protocol: ssh
          '';

      initialGlabConfig = ''
        git_protocol: ssh
        editor: vim
        browser: ""
        glamour_style: dark
        pager: ""
        check_update: false
        no_prompt: false
      ''
      + hostsSection;

      decryptedTokenFilePath = "${config.home.homeDirectory}/.secrets/glab-token";
      appendHostTokenCommand =
        if config.glab.gitlabHost == null then
          ""
        else
          ''
            if [ -s "${decryptedTokenFilePath}" ]; then
              printf '    token: %s\n' "$(cat "${decryptedTokenFilePath}")" >> "${glabConfigFile}"
            fi
          '';
    in
    {
      home.activation.setupGlabConfig = {
        after = [ "writeBoundary" ];
        before = [ ];
        data = ''
                mkdir -p "${glabConfigDir}"
                rm -f "${glabConfigFile}"
                cat > "${glabConfigFile}" << 'GLAB_CONFIG_EOF'
          ${initialGlabConfig}
          GLAB_CONFIG_EOF
                ${appendHostTokenCommand}
                chmod 600 "${glabConfigFile}"
        '';
      };

      healthCheck.probes = lib.optionals (config.glab.gitlabHost != null) [
        (healthCheckLib.mkBinaryProbe {
          name = "glab config holds a token for ${config.glab.gitlabHost}";
          command = "glab config get token --host ${config.glab.gitlabHost} | grep -q .";
        })
      ];
    };
}
