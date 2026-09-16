{
  pkgs,
  config,
  ...
}:
let
  homeDir = config.home.homeDirectory;

  twitterCli = import ./default.nix {
    inherit pkgs homeDir;
  };
in
{
  home.packages = twitterCli.packages;
}
