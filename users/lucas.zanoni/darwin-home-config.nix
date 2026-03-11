{ username, specialArgs, ... }:
{
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "backup";
    overwriteBackup = true;

    extraSpecialArgs = specialArgs // {
      inherit username;
    };
    users.${username} = import ./home-darwin.nix;
  };
}
