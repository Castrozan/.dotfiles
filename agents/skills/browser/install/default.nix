{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  inherit (pkgs.stdenv.hostPlatform) isDarwin;
  chromeDevtoolsMcpPackage = import ./chrome-devtools-mcp-package.nix {
    inherit pkgs nodejs;
  };
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpPackage}/bin/chrome-devtools-mcp";
  chromeGlobalUserDataDir =
    if isDarwin then
      "${homeDir}/Library/Application Support/Google/Chrome"
    else
      "${homeDir}/.config/chrome-global";

  supergatewayPackage = import ./supergateway-package.nix {
    inherit pkgs nodejs;
  };
  supergatewayBinary = "${supergatewayPackage}/bin/supergateway";

  pinchtabPackage = import ./pinchtab-package.nix {
    inherit pkgs;
  };
  pinchtabBinary = "${pinchtabPackage}/bin/pinchtab";

  chromeDevtoolsMcpStdioCommand = chromeDevtoolsMcpBinary;

  chromeDevtoolsMcpStdioArgs = [
    "--autoConnect"
    "--userDataDir"
    chromeGlobalUserDataDir
    "--usageStatistics"
    "false"
  ];
in
{
  inherit chromeDevtoolsMcpStdioCommand;
  inherit chromeDevtoolsMcpStdioArgs;
  inherit supergatewayBinary;
  inherit pinchtabBinary;

  packages = [ pinchtabPackage ];
}
