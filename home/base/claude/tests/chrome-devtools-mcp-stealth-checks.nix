{
  pkgs,
  lib,
  mkEvalCheck,
}:
let
  browserMcpInstall = import ../../../../agents/skills/browser/install {
    inherit pkgs;
    nodejs = pkgs.nodejs_22;
    homeDir = "/home/test-user";
    chromePackage = null;
  };

  chromeDevtoolsMcpPackage =
    import ../../../../agents/skills/browser/install/chrome-devtools-mcp-package.nix
      {
        inherit pkgs;
        nodejs = pkgs.nodejs_22;
      };

  chromeDevtoolsMcpArgsAttachByConsentToggle =
    (lib.elem "--autoConnect" browserMcpInstall.chromeDevtoolsMcpStdioArgs)
    && !(lib.any (
      argument: lib.hasPrefix "--browserUrl" argument
    ) browserMcpInstall.chromeDevtoolsMcpStdioArgs)
    && !(lib.any (
      argument: lib.hasInfix "--remote-debugging-port" argument
    ) browserMcpInstall.chromeDevtoolsMcpStdioArgs);

  chromeDevtoolsMcpMeetsAutoConnectVersionFloor =
    builtins.compareVersions chromeDevtoolsMcpPackage.version "1.6.0" >= 0;
in
{
  domain-claude-chrome-devtools-mcp-attaches-by-consent-toggle =
    mkEvalCheck "domain-claude-chrome-devtools-mcp-attaches-by-consent-toggle"
      chromeDevtoolsMcpArgsAttachByConsentToggle
      "the chrome-devtools MCP must attach with --autoConnect and never --browserUrl or --remote-debugging-port; the endpoint is exposed only by the user's manual Allow on chrome://inspect, which is the stealth and security model of this target, so an always-on debug port would both flag the browser as automated and let any local process drive the user's logged-in session";

  domain-claude-chrome-devtools-mcp-meets-autoconnect-version-floor =
    mkEvalCheck "domain-claude-chrome-devtools-mcp-meets-autoconnect-version-floor"
      chromeDevtoolsMcpMeetsAutoConnectVersionFloor
      "chrome-devtools-mcp must be pinned at 1.6.0 or newer; earlier pins call detectOpenDevToolsWindows on every tool call, which awaits hasDevTools across every page of a consent-attached browser and never resolves, so each tool call hangs forever against the user's real many-tabbed Chrome";
}
