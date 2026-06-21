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
  braveDefaultProfile = import ../../../../home/base/browser/brave-default-profile.nix {
    inherit (pkgs.stdenv.hostPlatform) isDarwin;
  };
  braveDefaultUserDataDir = "${homeDir}/${braveDefaultProfile.userDataDirectoryRelativeToHome}";

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

  braveDevtoolsMcpStdioCommand = chromeDevtoolsMcpBinary;
  braveDevtoolsMcpStdioArgs = mkChromeDevtoolsAutoConnectArgs braveDefaultUserDataDir;
in
{
  inherit chromeDevtoolsMcpStdioCommand;
  inherit chromeDevtoolsMcpStdioArgs;
  inherit braveDevtoolsMcpStdioCommand;
  inherit braveDevtoolsMcpStdioArgs;
  inherit pinchtabBinary;

  packages = [ pinchtabPackage ];
}
