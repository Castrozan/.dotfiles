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
    defaults.".GlobalPreferences"."com.apple.mouse.scaling" = 3.63;
  };

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
