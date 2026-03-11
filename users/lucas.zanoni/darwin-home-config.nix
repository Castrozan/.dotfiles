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
    users.${username} = import ./home-darwin.nix;
  };
}
