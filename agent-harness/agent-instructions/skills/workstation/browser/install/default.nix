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

  opencli = import ./opencli-jobs.nix { inherit pkgs nodejs; };

  mkChromeDevtoolsAutoConnectArgs = userDataDir: [
    "--autoConnect"
    "--userDataDir"
    userDataDir
    "--usageStatistics"
    "false"
  ];

  reserveStealthTargetForInteractiveSession = pkgs.writeShellScript "stealth-browser-mcp-interactive-only" ''
    if [ -n "''${CLAWDE_AGENT_NAME:-}" ]; then
      echo "stealth-browser-mcp: the consent-attached browser is reserved for the interactive session; autonomous clawde agents must use opencli-run with an isolated browser profile" >&2
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
  inherit (opencli) packages;
}
