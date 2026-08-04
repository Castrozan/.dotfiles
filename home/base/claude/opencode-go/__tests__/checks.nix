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

  linuxProxyService = linuxConfiguration.systemd.user.services.claude-go-proxy or null;
  darwinProxyAgents = map (
    configuration: configuration.launchd.agents.claude-go-proxy or null
  ) darwinConfigurations;
  linuxProxyCommand = builtins.concatStringsSep " " (
    lib.toList (linuxProxyService.Service.ExecStart or "")
  );
in
{
  opencode-go-linux-package =
    mkEvalCheck "opencode-go-linux-package" (hasPackage linuxConfiguration "claude-go")
      "Chise must install the claude-go launcher";

  opencode-go-darwin-packages = mkEvalCheck "opencode-go-darwin-packages" (builtins.all (
    configuration: hasPackage configuration "claude-go"
  ) darwinConfigurations) "Kira and Rin must install the claude-go launcher";

  opencode-go-linux-translation-proxy-service =
    mkEvalCheck "opencode-go-linux-translation-proxy-service"
      (linuxProxyService != null && linuxProxyService.Service.Restart == "always")
      "claude-go reaches Console Go only through the local translation proxy, so a host installing the launcher without an always-restarting proxy behind it ships a launcher that 400s on its first tool call";

  opencode-go-darwin-translation-proxy-agents =
    mkEvalCheck "opencode-go-darwin-translation-proxy-agents"
      (builtins.all (agent: agent != null && agent.config.KeepAlive) darwinProxyAgents)
      "the darwin hosts install the same launcher, so they need the same always-running translation proxy behind it";

  opencode-go-translation-proxy-takes-the-key-from-disk =
    mkEvalCheck "opencode-go-translation-proxy-takes-the-key-from-disk"
      (
        lib.hasInfix ".secrets/opencode-api-key" linuxProxyCommand
        && !(lib.hasInfix "api-key: " linuxProxyCommand)
      )
      "the proxy authenticates to the paid plan and every Nix store path is world readable, so its command must point at the agenix-deployed key file rather than carry the credential";
}
