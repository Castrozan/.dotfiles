{
  imports = [
    ./config-deployment/copy-rules-json-to-user-config-directory.nix
    ./config-deployment/kick-console-user-server-every-rebuild.nix
    ./restart-on-wake/launchd-agent.nix
    ./orphan-launchd-cleanup/home-manager-activation.nix
    ./status/home-manager-binary.nix
  ];
}
