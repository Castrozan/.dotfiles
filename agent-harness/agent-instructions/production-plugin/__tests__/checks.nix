{
  pkgs,
  lib,
  helpers,
  ...
}:
let
  source = import ../. {
    inherit pkgs lib;
    hostname = "test";
    homeDirectory = "/home/test";
    chromePackage = pkgs.google-chrome;
    isDarwin = false;
  };
  bundle = (import ../../../plugin-distribution { inherit pkgs; }).buildPlugin {
    inherit source;
    opencodeDataRoot = "/home/test/.local/state/agent-plugins/opencode";
  };
  servers = import ../mcp-servers.nix {
    inherit pkgs;
  };
  desktopPackages = (import ../../skills/workstation/desktop/install { inherit pkgs; }).packages;
in
{
  production-plugin-desktop-platform = helpers.mkEvalCheck "production-plugin-desktop-platform" (
    (servers ? desktop-computer-use) == pkgs.stdenv.hostPlatform.isDarwin
    && (desktopPackages != [ ]) == pkgs.stdenv.hostPlatform.isDarwin
  ) "The desktop MCP and runtime must be present only on macOS";

  production-plugin-artifact-preservation =
    pkgs.runCommand "production-plugin-artifact-preservation" { }
      ''
        ${pkgs.python312}/bin/python3 ${./verify-production-bundle.py} ${bundle}
        touch "$out"
      '';
}
