{ ... }:
{
  imports = [
    ../shared-darwin-configuration.nix
  ];

  services.tailscale.enable = true;

  homebrew.casks = [
    "claude"
    "codex-app"
    "firefox"
    "mongodb-compass"
  ];
}
