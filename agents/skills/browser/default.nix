{ pkgs, ... }:
let
  playwrightNodeModules = pkgs.runCommand "pw-node-modules" { } ''
    mkdir -p $out/node_modules
    ln -s ${pkgs.playwright-driver} $out/node_modules/playwright-core
  '';
in
{
  inherit playwrightNodeModules;

  playwrightBrowsersPath = "${pkgs.playwright-driver.browsers}";
}
