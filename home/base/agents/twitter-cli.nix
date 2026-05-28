{
  pkgs,
  config,
  ...
}:
let
  homeDir = config.home.homeDirectory;

  twitterCli = import ../../../agents/skills/comms/skills/twitter/install {
    inherit pkgs homeDir;
  };
in
{
  home.packages = twitterCli.packages;
}
