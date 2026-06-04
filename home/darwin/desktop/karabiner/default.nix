{
  imports = [
    ./config-deployment/copy-rules-json-to-user-config-directory.nix
    ./config-deployment/kick-karabiner-user-agents-when-config-changed.nix
    ./restart-on-wake/launchd-agent.nix
    ./orphan-launchd-cleanup/home-manager-activation.nix
    ./status/home-manager-binary.nix
    ./health.nix
  ];
}
