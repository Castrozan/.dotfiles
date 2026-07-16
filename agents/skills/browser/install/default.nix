{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  chromeDevtoolsMcpPackage = import ./chrome-devtools-mcp-package.nix {
    inherit pkgs nodejs;
  };
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpPackage}/bin/chrome-devtools-mcp";
  chromeGlobalUserDataDir = "${homeDir}/.config/chrome-global";
  vivaldiDefaultProfile = import ../../../../home/base/browser/vivaldi-default-profile.nix {
    inherit (pkgs.stdenv.hostPlatform) isDarwin;
  };
  vivaldiDefaultUserDataDir = "${homeDir}/${vivaldiDefaultProfile.userDataDirectoryRelativeToHome}";

  pinchtabPackage = import ./pinchtab-package.nix {
    inherit pkgs;
  };
  pinchtabBinary = "${pinchtabPackage}/bin/pinchtab";

  mkChromeDevtoolsAutoConnectArgs = userDataDir: [
    "--autoConnect"
    "--userDataDir"
    userDataDir
    "--usageStatistics"
    "false"
  ];

  chromeDevtoolsMcpStdioCommand = chromeDevtoolsMcpBinary;
  chromeDevtoolsMcpStdioArgs = mkChromeDevtoolsAutoConnectArgs chromeGlobalUserDataDir;

  vivaldiDevtoolsMcpStdioCommand = chromeDevtoolsMcpBinary;
  vivaldiDevtoolsMcpStdioArgs = mkChromeDevtoolsAutoConnectArgs vivaldiDefaultUserDataDir;
in
{
  inherit chromeDevtoolsMcpStdioCommand;
  inherit chromeDevtoolsMcpStdioArgs;
  inherit vivaldiDevtoolsMcpStdioCommand;
  inherit vivaldiDevtoolsMcpStdioArgs;
  inherit pinchtabBinary;

  packages = [ pinchtabPackage ];
}
