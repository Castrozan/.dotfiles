{
  hostname,
  username,
  specialArgs,
  sharedModules ? [ ],
}:
{
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "backup";
    overwriteBackup = true;
    inherit sharedModules;
    extraSpecialArgs = specialArgs;
    users.${username} = import ../../machine-configuration/machines/${hostname}/home.nix;
  };
}
