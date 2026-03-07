{ config, ... }:
let
  glabConfigDir = "${config.home.homeDirectory}/.config/glab-cli";
  glabConfigFile = "${glabConfigDir}/config.yml";

  initialGlabConfig = ''
    git_protocol: ssh
    editor: vim
    browser: ""
    glamour_style: dark
    pager: ""
    check_update: false
    no_prompt: false

    hosts:
      gitlab.services.betha.cloud:
        api_host: gitlab.services.betha.cloud
        git_protocol: ssh
  '';
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
}
