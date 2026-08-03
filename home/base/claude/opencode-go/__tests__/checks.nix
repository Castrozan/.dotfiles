{
  pkgs,
  lib,
  mkEvalCheck,
  helpers,
  self,
}:
let
  linuxConfiguration = helpers.homeManagerTestConfigurationForLinuxHost "chise" [
    self.homeManagerModules.claude-code
  ];

  darwinConfigurations =
    map
      (
        hostname:
        helpers.homeManagerTestConfigurationForDarwinHost hostname [
          self.homeManagerModules.claude-code
        ]
      )
      [
        "kira"
        "rin"
      ];

  hasPackage =
    configuration: packageName:
    builtins.any (package: lib.getName package == packageName) configuration.home.packages;
in
{
  opencode-go-linux-package =
    mkEvalCheck "opencode-go-linux-package" (hasPackage linuxConfiguration "claude-go")
      "Chise must install the claude-go launcher";

  opencode-go-darwin-packages = mkEvalCheck "opencode-go-darwin-packages" (builtins.all (
    configuration: hasPackage configuration "claude-go"
  ) darwinConfigurations) "Kira and Rin must install the claude-go launcher";
}
