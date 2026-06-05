{ ... }:
{
  imports = [
    ../shared-darwin-configuration.nix
  ];

  services.tailscale.enable = true;

  homebrew.casks = [
    "firefox"
  ];
}
