{
  pkgs,
  homeDirectory,
  chromePackage,
}:
let
  browser = import ../skills/workstation/browser/install {
    inherit pkgs chromePackage;
    nodejs = pkgs.nodejs_22;
    homeDir = homeDirectory;
  };
  sonarqube =
    import ../../../machine-configuration/development/testing/sonarqube/sonarqube-tools.nix
      {
        inherit pkgs;
      };
  desktopComputerUse = import ../skills/workstation/desktop/install { inherit pkgs; };
in
{
  chrome-devtools = {
    type = "stdio";
    command = browser.chromeDevtoolsMcpStdioCommand;
    args = browser.chromeDevtoolsMcpStdioArgs;
  };
  desktop-computer-use = {
    type = "stdio";
    command = pkgs.lib.getExe desktopComputerUse;
  };
  sonarqube = {
    type = "stdio";
    command = "${sonarqube.mcp}/bin/sonarqube-mcp";
    env.SONARQUBE_TOKEN_FILE = "${homeDirectory}/.secrets/sonarqube-token";
  };
}
