# Zanoni's Home Manager Configuration
{ username, specialArgs, ... }:
{
  home-manager.useGlobalPkgs = true;
  home-manager.useUserPackages = true;
  home-manager.backupFileExtension = "backup";

  home-manager.extraSpecialArgs = specialArgs // {
    inherit username;
  };
  home-manager.users.${username} = import ./home.nix;
}
