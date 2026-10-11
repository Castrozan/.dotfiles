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
  desktopComputerUse = import ../skills/workstation/desktop/install/computer-use-mcp-package.nix {
    inherit pkgs;
  };
in
{
  chrome-devtools = {
    type = "stdio";
    command = browser.chromeDevtoolsMcpStdioCommand;
    args = browser.chromeDevtoolsMcpStdioArgs;
  };
}
// pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
  desktop-computer-use = {
    type = "stdio";
    command = pkgs.lib.getExe desktopComputerUse;
  };
}
