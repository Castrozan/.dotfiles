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
        helpers.homeManagerTestConfigurationForDarwinHost hostname [
          self.homeManagerModules.claude-code
        ]
      )
      [
        "kira"
        "rin"
      ];

  allConfigurations = [ linuxConfiguration ] ++ darwinConfigurations;

  hasPackage =
    configuration: packageName:
    builtins.any (package: lib.getName package == packageName) configuration.home.packages;

  linuxCliProxyApiPackage = builtins.head (
    builtins.filter (package: lib.getName package == "cli-proxy-api") linuxConfiguration.home.packages
  );
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
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  claudex-linux-proxy-binary = pkgs.runCommandLocal "check-claudex-linux-proxy-binary" { } ''
    test -x ${linuxCliProxyApiPackage}/bin/cli-proxy-api
    touch $out
  '';
}
