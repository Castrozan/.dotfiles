{ latest, ... }:
{
  imports = [
    ../../shared-darwin-system-nix-darwin.nix
    ../../../network/ipv6/ipv6-link-local-nix-darwin.nix
  ];

  services.tailscale = {
    enable = true;
    package = latest.tailscale;
  };

  homebrew.casks = [
    "claude"
    "firefox"
    "mongodb-compass"
  ];
}
