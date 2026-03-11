{ pkgs, username, ... }:
{
  users.users.${username} = {
    name = username;
    home = "/Users/${username}";
    shell = pkgs.fish;
  };

  system = {
    primaryUser = username;
    stateVersion = 6;
    keyboard = {
      enableKeyMapping = true;
      userKeyMapping = [
        {
          HIDKeyboardModifierMappingSrc = 30064771121;
          HIDKeyboardModifierMappingDst = 30064771124;
        }
      ];
    };
    defaults = {
      ".GlobalPreferences"."com.apple.mouse.scaling" = 3.63;
      NSGlobalDomain.AppleInterfaceStyle = "Dark";
      dock = {
        autohide = true;
        show-recents = false;
        tilesize = 48;
        minimize-to-application = true;
        mru-spaces = false;
      };
    };
  };

  system.activationScripts.postActivation.text = ''
    osascript -e 'tell application "System Events" to tell every desktop to set picture to "/Users/${username}/.dotfiles/static/alter-jellyfish-dark.jpg"'
  '';

  programs.fish.enable = true;

  security = {
    pam.services.sudo_local.touchIdAuth = true;
    sudo.extraConfig = ''
      ${username} ALL=(ALL) NOPASSWD: /run/current-system/sw/bin/darwin-rebuild
    '';
  };

  nixpkgs = {
    config.allowUnfree = true;
    hostPlatform = "aarch64-darwin";
  };
}
