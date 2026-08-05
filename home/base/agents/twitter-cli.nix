{
  pkgs,
  config,
  ...
}:
let
  homeDir = config.home.homeDirectory;

  twitterCli = import ../../../agent-harness/agent-instructions/skills/twitter/install {
    inherit pkgs homeDir;
  };
in
{
  home.packages = twitterCli.packages;
}
