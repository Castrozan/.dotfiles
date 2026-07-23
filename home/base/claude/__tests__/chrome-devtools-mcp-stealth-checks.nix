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

  chromeDevtoolsMcpArgsAttachByConsentToggle =
    (lib.elem "--autoConnect" browserMcpInstall.chromeDevtoolsMcpStdioArgs)
    && !(lib.any (
      argument: lib.hasPrefix "--browserUrl" argument
    ) browserMcpInstall.chromeDevtoolsMcpStdioArgs)
    && !(lib.any (
      argument: lib.hasInfix "--remote-debugging-port" argument
    ) browserMcpInstall.chromeDevtoolsMcpStdioArgs);

  stealthTargetReservedForInteractiveSession = lib.hasInfix "stealth-browser-mcp-interactive-only" (
    toString browserMcpInstall.chromeDevtoolsMcpStdioCommand
  );

in
{
  domain-claude-chrome-devtools-mcp-attaches-by-consent-toggle =
    mkEvalCheck "domain-claude-chrome-devtools-mcp-attaches-by-consent-toggle"
      chromeDevtoolsMcpArgsAttachByConsentToggle
      "the chrome-devtools MCP must attach with --autoConnect and never --browserUrl or --remote-debugging-port; the endpoint is exposed only by the user's manual Allow on chrome://inspect, which is the stealth and security model of this target, so an always-on debug port would both flag the browser as automated and let any local process drive the user's logged-in session";

  domain-claude-stealth-cdp-target-reserved-for-interactive-session =
    mkEvalCheck "domain-claude-stealth-cdp-target-reserved-for-interactive-session"
      stealthTargetReservedForInteractiveSession
      "the chrome stealth CDP command must route through the stealth-browser-mcp-interactive-only gate wrapper so an autonomous clawde agent (which carries CLAWDE_RESUME_FLAG in its environment, unlike an interactive session) never attaches to the user's single-client consent-gated browser and knocks the interactive session off; autonomous agents use pinchtab for browsing instead";
}
