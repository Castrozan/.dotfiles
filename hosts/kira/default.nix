{ ... }:
{
  imports = [
    ../shared-darwin-configuration.nix
    ./brave
    ./wezterm
    ./displays
    ./finder
    ./window-manager
    ./symbolic-hotkeys
    ./quit-windowless-applications
    ./workspace-window-switcher
    ./rebuild
    ./karabiner
  ];

  system.defaults.NSGlobalDomain."com.apple.swipescrolldirection" = true;

  services.tailscale.enable = true;

  homebrew.casks = [
    "firefox"
  ];
}
