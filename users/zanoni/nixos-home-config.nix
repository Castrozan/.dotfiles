# Zanoni's Home Manager Configuration
{ username, specialArgs, ... }:
{
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    # Use static extension + overwrite to prevent backup file accumulation
    backupFileExtension = "backup";
    overwriteBackup = true;

    extraSpecialArgs = specialArgs // {
      inherit username;
    };
    users.${username} = import ./home.nix;
  };
}
