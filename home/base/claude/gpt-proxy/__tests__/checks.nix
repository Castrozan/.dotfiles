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

  linuxCliProxyApiPackage = builtins.head (
    builtins.filter (package: lib.getName package == "cli-proxy-api") linuxConfiguration.home.packages
  );
in
{
  claude-gpt-linux-packages = mkEvalCheck "claude-gpt-linux-packages" (
    hasPackage linuxConfiguration "claude-gpt"
    && hasPackage linuxConfiguration "claude-gpt-login"
    && hasPackage linuxConfiguration "cli-proxy-api"
  ) "Chise must install the claude-gpt launchers and cli-proxy-api package";

  claude-gpt-linux-systemd-service = mkEvalCheck "claude-gpt-linux-systemd-service" (
    linuxConfiguration.systemd.user.services ? cli-proxy-api
    && lib.hasInfix "cli-proxy-api-ipv4-gateway.py" linuxConfiguration.systemd.user.services.cli-proxy-api.Service.ExecStart
  ) "Chise must run cli-proxy-api as a systemd user service";

  claude-gpt-darwin-packages = mkEvalCheck "claude-gpt-darwin-packages" (builtins.all
    (
      configuration:
      hasPackage configuration "claude-gpt"
      && hasPackage configuration "claude-gpt-login"
      && hasPackage configuration "cli-proxy-api"
    )
    darwinConfigurations
  ) "Rin and Kira must install the claude-gpt launchers and cli-proxy-api package";

  claude-gpt-darwin-launchd-agent = mkEvalCheck "claude-gpt-darwin-launchd-agent" (builtins.all (
    configuration:
    configuration.launchd.agents ? cli-proxy-api
    && builtins.any (lib.hasSuffix "cli-proxy-api-ipv4-gateway.py") configuration.launchd.agents.cli-proxy-api.config.ProgramArguments
  ) darwinConfigurations) "Rin and Kira must run cli-proxy-api through the IPv4 gateway";
}
// lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  claude-gpt-linux-proxy-binary = pkgs.runCommandLocal "check-claude-gpt-linux-proxy-binary" { } ''
    test -x ${linuxCliProxyApiPackage}/bin/cli-proxy-api
    touch $out
  '';
}
