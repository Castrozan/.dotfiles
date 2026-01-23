# Zanoni's Home Manager Configuration
{ username, specialArgs, ... }:
{
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "backup";

    extraSpecialArgs = specialArgs // {
      inherit username;
    };
    users.${username} = import ./home.nix;
  };
}
