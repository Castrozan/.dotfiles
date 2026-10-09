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
}
