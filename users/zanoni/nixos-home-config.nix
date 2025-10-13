# Zanoni's Home Manager Configuration
{
  username,
  specialArgs,
  inputs,
  ...
}:
{
  home-manager.useGlobalPkgs = true;
  home-manager.useUserPackages = true;
  home-manager.backupFileExtension = "backup";

  home-manager.extraSpecialArgs = specialArgs // {
    inherit username;
  };
  home-manager.sharedModules = [
    inputs.caelestia-shell.homeManagerModules.default
  ];
  home-manager.users.${username} = import ./home.nix;
}
