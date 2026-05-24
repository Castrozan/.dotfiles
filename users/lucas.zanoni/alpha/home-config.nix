{
  username,
  hostname,
  nixpkgs-version,
  home-version,
  inputs,
  unstable,
  latest,
  isNixOS,
  isDarwin,
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
        hostname
        isNixOS
        isDarwin
        ;
    };
    users.${username} = import ./home.nix;
  };
}
