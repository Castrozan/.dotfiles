{ config, ... }:
let
  glabConfigDir = "${config.home.homeDirectory}/.config/glab-cli";
  glabConfigFile = "${glabConfigDir}/config.yml";

  # Initial config content - glab needs 600 permissions to write tokens
  initialConfig = ''
    # GitLab CLI configuration
    # See: https://gitlab.com/gitlab-org/cli/-/blob/main/docs/source/configuration.md

    git_protocol: ssh
    editor: vim
    browser: ""
    glamour_style: dark
    pager: ""
    check_update: false
    no_prompt: false

    hosts:
      gitlab.services.betha.cloud:
        # Token will be set after running: glab auth login --hostname gitlab.services.betha.cloud
        api_host: gitlab.services.betha.cloud
        git_protocol: ssh
  '';
in
{
  # glab (GitLab CLI) configuration
  # Package is installed via pkgs.nix
  #
  # After home-manager switch, authenticate with:
  #   glab auth login --hostname gitlab.services.betha.cloud
  #
  # This will prompt for a personal access token. Create one at:
  #   https://gitlab.services.betha.cloud/-/user_settings/personal_access_tokens
  # Required scopes: api, read_user, read_repository, write_repository

  # Use activation script instead of xdg.configFile because glab needs
  # write access (600 permissions) to store authentication tokens.
  # xdg.configFile creates immutable 444 files.
  home.activation.setupGlabConfig = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
            # Create config directory if it doesn't exist
            mkdir -p "${glabConfigDir}"

            # Remove symlink if it exists (from previous xdg.configFile management)
            if [ -L "${glabConfigFile}" ]; then
              rm "${glabConfigFile}"
            fi

            # Only create config if it doesn't exist (preserve user tokens)
            if [ ! -f "${glabConfigFile}" ]; then
              cat > "${glabConfigFile}" << 'GLAB_CONFIG_EOF'
      ${initialConfig}
      GLAB_CONFIG_EOF
              chmod 600 "${glabConfigFile}"
              echo "Created glab config at ${glabConfigFile}"
            else
              # Ensure correct permissions even if file exists
              chmod 600 "${glabConfigFile}" 2>/dev/null || true
            fi
    '';
  };
}
