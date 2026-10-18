{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  chromeDevtoolsCli = import ./chrome-devtools-cli.nix {
    inherit
      pkgs
      homeDir
      nodejs
      chromePackage
      ;
  };
  opencli = import ./opencli-jobs.nix { inherit pkgs nodejs; };
in
{
  inherit chromeDevtoolsCli;
  packages = [ chromeDevtoolsCli ] ++ opencli.packages;
}
