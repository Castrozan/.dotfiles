{ pkgs, username, ... }:
{
  users.users.${username} = {
    name = username;
    home = "/Users/${username}";
    shell = pkgs.fish;
  };

  system.primaryUser = username;

  system.keyboard.enableKeyMapping = true;
  system.keyboard.userKeyMapping = [
    {
      HIDKeyboardModifierMappingSrc = 30064771121;
      HIDKeyboardModifierMappingDst = 30064771124;
    }
  ];

  system.defaults.".GlobalPreferences"."com.apple.mouse.scaling" = 3.0;

  programs.fish.enable = true;
  security.pam.services.sudo_local.touchIdAuth = true;
  security.sudo.extraConfig = ''
    ${username} ALL=(ALL) NOPASSWD: /run/current-system/sw/bin/darwin-rebuild
  '';

  nixpkgs.config.allowUnfree = true;
  system.stateVersion = 6;
  nixpkgs.hostPlatform = "aarch64-darwin";
}
