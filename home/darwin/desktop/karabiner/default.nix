{
  imports = [
    ./config-deployment/copy-rules-json-to-user-config-directory.nix
    ./config-deployment/kick-karabiner-user-agents-every-rebuild.nix
    ./restart-on-wake/launchd-agent.nix
    ./orphan-launchd-cleanup/home-manager-activation.nix
    ./status/home-manager-binary.nix
    ./health.nix
  ];
}
