{
  username,
  nixpkgs-version,
  home-version,
  inputs,
  unstable,
  latest,
  isNixOS,
  ...
}:
{
  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "backup";
    overwriteBackup = true;
    sharedModules = [ inputs.stylix.homeModules.stylix ];

    extraSpecialArgs = {
      inherit
        nixpkgs-version
        home-version
        inputs
        unstable
        latest
        username
        isNixOS
        ;
    };
    users.${username} = import ./home.nix;
  };
}
