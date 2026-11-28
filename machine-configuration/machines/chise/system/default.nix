{
  imports = [
    ./configs/configuration.nix

    ./configs/hardware-configuration.nix

    ./nixos-system.nix

    ../../../network/ssh/ssh-config-ownership-nixos.nix
    ../../../browsers/brave/chise-brave-policy-nixos.nix
  ];
}
