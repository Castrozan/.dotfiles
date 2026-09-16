{
  pkgs,
  lib,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  linuxConfiguration = helpers.homeManagerTestConfigurationForLinuxHost "chise" [
    self.homeManagerModules.claude-code
  ];

  darwinConfigurations =
    map
      (
        hostname:
        helpers.homeManagerTestConfigurationForDarwinHost hostname (
          [ self.homeManagerModules.claude-code ]
          ++ lib.optional (hostname == "rin") {
            claude.requiredWorkspaceProfileName = "mcd-ca";
          }
        )
      )
      [
        "kira"
        "rin"
      ];

  allConfigurations = [ linuxConfiguration ] ++ darwinConfigurations;

  rinConfiguration = builtins.elemAt darwinConfigurations 1;

  hasPackage =
    configuration: packageName:
    builtins.any (package: lib.getName package == packageName) configuration.home.packages;

  linuxCliProxyApiPackage = builtins.head (
    builtins.filter (package: lib.getName package == "cli-proxy-api") linuxConfiguration.home.packages
  );

  rinClaudexPackage = builtins.head (
    builtins.filter (package: lib.getName package == "claudex") rinConfiguration.home.packages
  );

  executableText = package: builtins.unsafeDiscardStringContext "${package}/bin/claude";
in
{
  claudex-packages = mkEvalCheck "claudex-packages" (builtins.all (
    configuration:
    hasPackage configuration "claudex"
    && hasPackage configuration "claudex-login"
    && hasPackage configuration "cli-proxy-api"
  ) allConfigurations) "Supported hosts must install the claudex launchers and cli-proxy-api package";

  claudex-linux-systemd-service = mkEvalCheck "claudex-linux-systemd-service" (
    linuxConfiguration.systemd.user.services ? cli-proxy-api
    && lib.hasInfix "cli-proxy-api-ipv4-gateway.py" (
      lib.concatStringsSep " " (
        lib.toList linuxConfiguration.systemd.user.services.cli-proxy-api.Service.ExecStart
      )
    )
  ) "Chise must run cli-proxy-api as a systemd user service";

  claudex-darwin-launchd-agent = mkEvalCheck "claudex-darwin-launchd-agent" (builtins.all (
    configuration:
    configuration.launchd.agents ? cli-proxy-api
    && builtins.any (lib.hasSuffix "cli-proxy-api-ipv4-gateway.py") configuration.launchd.agents.cli-proxy-api.config.ProgramArguments
  ) darwinConfigurations) "Rin and Kira must run cli-proxy-api through the IPv4 gateway";

  claudex-rin-launches-the-unrestricted-interactive-package =
    mkEvalCheck "claudex-rin-launches-the-unrestricted-interactive-package"
      (
        lib.hasInfix (executableText rinConfiguration.claude.unrestrictedInteractivePackage) rinClaudexPackage.text
        && !(lib.hasInfix (executableText rinConfiguration.claude.package) rinClaudexPackage.text)
      )
      "claudex uses a different provider and must remain available outside Rin's MCD-only plain claude command";
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  claudex-linux-proxy-binary = pkgs.runCommandLocal "check-claudex-linux-proxy-binary" { } ''
    test -x ${linuxCliProxyApiPackage}/bin/cli-proxy-api
    touch $out
  '';
}
