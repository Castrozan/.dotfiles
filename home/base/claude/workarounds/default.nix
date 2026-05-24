{ ... }:
{
  imports = [
    ./make-settings-json-mutable-because-home-manager-symlinks-are-readonly.nix
    ./disable-auto-updater-by-forcing-install-method-native.nix
  ];
}
