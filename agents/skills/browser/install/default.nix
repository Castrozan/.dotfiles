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

  reserveStealthTargetForInteractiveSession = pkgs.writeShellScript "stealth-browser-mcp-interactive-only" ''
    if [ -n "''${CLAWDE_RESUME_FLAG:-}" ]; then
      echo "stealth-browser-mcp: the consent-attached browser is a single-client target reserved for the interactive session; refusing to attach from an autonomous clawde agent so the agent fleet never contends for the user's real logged-in browser (use pinchtab for autonomous browsing)" >&2
      exit 0
    fi
    exec ${chromeDevtoolsMcpBinary} "$@"
  '';

  chromeDevtoolsMcpStdioCommand = reserveStealthTargetForInteractiveSession;
  chromeDevtoolsMcpStdioArgs = mkChromeDevtoolsAutoConnectArgs chromeGlobalUserDataDir;
in
{
  inherit chromeDevtoolsMcpStdioCommand;
  inherit chromeDevtoolsMcpStdioArgs;
  inherit pinchtabBinary;

  packages = [ pinchtabPackage ];
}
