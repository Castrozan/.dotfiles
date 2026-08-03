{
  pkgs,
  lib,
  mkEvalCheck,
  helpers,
  self,
}:
let
  opencodeGoModel = "qwen3.7-plus";
  opencodeGoBaseUrl = "https://opencode.ai/zen/go";

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
  firstDarwinConfiguration = builtins.head darwinConfigurations;

  hasPackage =
    configuration: packageName:
    builtins.any (package: lib.getName package == packageName) configuration.home.packages;

  claudeGoLauncherPackageFrom =
    configuration:
    let
      launcherCandidates = builtins.filter (
        package: lib.getName package == "claude-go"
      ) configuration.home.packages;
    in
    if launcherCandidates == [ ] then
      builtins.throw "the claude-go launcher is missing from home.packages; the opencode-go module host gate must include this host"
    else
      builtins.head launcherCandidates;

  bakedClaudeBinaryPathFrom = configuration: "${configuration.claude.package}/bin/claude";

  runLauncherScriptContractCheck =
    name: configuration:
    pkgs.runCommandLocal "check-${name}" { } ''
      ${../scripts/check-launcher-script-contract.sh} \
        ${claudeGoLauncherPackageFrom configuration}/bin/claude-go \
        ${opencodeGoModel} \
        ${opencodeGoBaseUrl} \
        ${bakedClaudeBinaryPathFrom configuration}
      touch $out
    '';

  runMissingSecretCheck =
    name: configuration:
    pkgs.runCommandLocal "check-${name}" { } ''
      ${../scripts/check-launcher-missing-secret.sh} ${claudeGoLauncherPackageFrom configuration}/bin/claude-go
      touch $out
    '';

  runLaunchContractCheck =
    name: configuration:
    pkgs.runCommandLocal "check-${name}" { } ''
      ${../scripts/check-launcher-launch-contract.sh} \
        ${claudeGoLauncherPackageFrom configuration}/bin/claude-go \
        ${bakedClaudeBinaryPathFrom configuration} \
        ${opencodeGoModel} \
        ${opencodeGoBaseUrl}
      touch $out
    '';
in
{
  opencode-go-linux-package =
    mkEvalCheck "opencode-go-linux-package" (hasPackage linuxConfiguration "claude-go")
      "Chise must install the claude-go launcher";

  opencode-go-darwin-packages = mkEvalCheck "opencode-go-darwin-packages" (builtins.all (
    configuration: hasPackage configuration "claude-go"
  ) darwinConfigurations) "Kira and Rin must install the claude-go launcher";
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  opencode-go-linux-launcher-script-contract = runLauncherScriptContractCheck "opencode-go-linux-launcher-script-contract" linuxConfiguration;

  opencode-go-linux-launcher-fails-without-the-secret = runMissingSecretCheck "opencode-go-linux-launcher-fails-without-the-secret" linuxConfiguration;

  opencode-go-linux-launch-contract = runLaunchContractCheck "opencode-go-linux-launch-contract" linuxConfiguration;
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
  opencode-go-darwin-launcher-script-contract = runLauncherScriptContractCheck "opencode-go-darwin-launcher-script-contract" firstDarwinConfiguration;

  opencode-go-darwin-launcher-fails-without-the-secret = runMissingSecretCheck "opencode-go-darwin-launcher-fails-without-the-secret" firstDarwinConfiguration;

  opencode-go-darwin-launch-contract = runLaunchContractCheck "opencode-go-darwin-launch-contract" firstDarwinConfiguration;
}
