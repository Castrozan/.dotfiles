{
  config,
  lib,
  ...
}:
let
  privateConfigRoot = ../../../private-config;
  workpcPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = lib.optionals workpcPrivateConfigExists [
    "${privateConfigRoot}/machines/workpc/glab-host.nix"
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

                if [ -L "${glabConfigFile}" ]; then
                  rm "${glabConfigFile}"
                fi

                if [ ! -f "${glabConfigFile}" ]; then
                  cat > "${glabConfigFile}" << 'GLAB_CONFIG_EOF'
          ${initialGlabConfig}
          GLAB_CONFIG_EOF
                  chmod 600 "${glabConfigFile}"
                  echo "Created glab config at ${glabConfigFile}"
                else
                  chmod 600 "${glabConfigFile}" 2>/dev/null || true
                fi
        '';
      };
    };
}
