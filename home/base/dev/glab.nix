{
  config,
  lib,
  hostname,
  healthCheckLib,
  ...
}:
let
  privateConfigRoot = ../../../private-config;
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
    description = "Optional hosts.<host> entry for glab-cli. Set in private-config when the host is non-public.";
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
                chmod 600 "${glabConfigFile}"
        '';
      };

      healthCheck.probes = [
        (healthCheckLib.mkBinaryProbe {
          name = "glab auth recognises configured host + token";
          command = ". $HOME/.secrets/source-secrets.sh 2>/dev/null; glab auth status 2>&1 | grep -q 'Token found'";
        })
      ];
    };
}
