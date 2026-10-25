{
  helpers,
  lib,
  inputs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  composedDarwinConfiguration =
    (inputs.nix-darwin.lib.darwinSystem {
      modules = [
        ../homebrew-undeclared-package-cleanup-nix-darwin.nix
        {
          nixpkgs.hostPlatform = "aarch64-darwin";
          system = {
            stateVersion = 6;
            primaryUser = "test-user";
          };
          homebrew = {
            enable = true;
            casks = [ "chatgpt" ];
          };
        }
      ];
    }).config;
  homebrewActivation = composedDarwinConfiguration.system.activationScripts.homebrew.text;
  bundleInstallPosition = lib.strings.stringLength (
    builtins.head (lib.splitString "Homebrew uninstalling undeclared packages" homebrewActivation)
  );
  cleanupRunsAfterBundleInstall =
    lib.hasInfix "brew bundle --file=" (builtins.substring 0 bundleInstallPosition homebrewActivation)
    && lib.hasInfix "brew bundle cleanup --force --file=" homebrewActivation
    && lib.hasInfix "--user=test-user" homebrewActivation
    && lib.hasInfix "if [ -f \"/opt/homebrew/bin/brew\" ]" homebrewActivation
    && composedDarwinConfiguration.homebrew.onActivation.cleanup == "none";
in
{
  darwin-homebrew-uninstalls-undeclared-packages =
    mkEvalCheck "darwin-homebrew-uninstalls-undeclared-packages" cleanupRunsAfterBundleInstall
      "Darwin homebrew activation must run brew bundle cleanup --force against the declared Brewfile after the bundle install, guarded on brew existing, because Homebrew 7 removed the --cleanup switch that nix-darwin 25.11 passes for onActivation.cleanup";
}
