{
  pkgs,
  lib,
  mkEvalCheck,
}:
let
  browser = import ../../../agent-instructions/skills/workstation/browser/install {
    inherit pkgs;
    nodejs = pkgs.nodejs_22;
    homeDir = "/home/test-user";
    chromePackage = pkgs.writeShellScriptBin "google-chrome-stable" "exit 1";
  };
  servers = import ../../../agent-instructions/production-plugin/mcp-servers.nix {
    inherit pkgs;
  };
in
{
  domain-browser-chrome-devtools-is-not-an-automatic-mcp-server =
    mkEvalCheck "domain-browser-chrome-devtools-is-not-an-automatic-mcp-server"
      (!(servers ? chrome-devtools))
      "Chrome DevTools must run through the on-demand CLI rather than spawning an MCP server with every agent session";

  domain-browser-chrome-devtools-cli-is-installed =
    mkEvalCheck "domain-browser-chrome-devtools-cli-is-installed"
      (lib.elem browser.chromeDevtoolsCli browser.packages)
      "the shared browser capability must install its managed CLI on every configured host";

  domain-browser-chrome-devtools-headless-executable-matches-platform =
    mkEvalCheck "domain-browser-chrome-devtools-headless-executable-matches-platform"
      (
        if pkgs.stdenv.hostPlatform.isDarwin then
          browser.chromeDevtoolsCli.configuration.chromeExecutable
          == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        else
          lib.hasSuffix "/bin/google-chrome-stable" browser.chromeDevtoolsCli.configuration.chromeExecutable
      )
      "headless Chrome must use the native application on macOS and the declared Chrome package on NixOS";
}
