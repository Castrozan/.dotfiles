{ pkgs, homeManager }:
let
  homeDirectory = if pkgs.stdenv.isDarwin then "/Users/test" else "/home/test";
  module = ../chromium-bitwarden-home-manager.nix;
  evaluate =
    modules:
    (homeManager.lib.homeManagerConfiguration {
      inherit pkgs;
      modules = [
        {
          home = {
            username = "test";
            inherit homeDirectory;
            stateVersion = "25.11";
          };
        }
      ]
      ++ modules;
    }).config;
in
{
  baseline = evaluate [ ];
  configured = evaluate [ module ];
  customXdg = evaluate [
    module
    { xdg.configHome = "${homeDirectory}/configuration"; }
  ];
  conflictingPackage = evaluate [
    module
    { programs.chromium.package = pkgs.hello; }
  ];
  conflictingFlags = evaluate [
    module
    { programs.chromium.commandLineArgs = [ "--example" ]; }
  ];
}
