{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  linuxConfiguration = helpers.homeManagerTestConfiguration [ ../herdr-home-manager.nix ];
  darwinConfiguration = helpers.homeManagerTestConfigurationForDarwin [ ../herdr-home-manager.nix ];
  linuxService = linuxConfiguration.systemd.user.services.herdr;
  darwinAgent = darwinConfiguration.launchd.agents.herdr;
  darwinAgentProgram = builtins.head darwinAgent.config.ProgramArguments;
  darwinAgentPreservation = darwinConfiguration.home.activation."preserveRunningLaunchAgent-herdr";
  linuxAdoption = linuxConfiguration.home.activation.adoptLegacyHerdrServer;
  linuxReconciliation = linuxConfiguration.home.activation.reconcileHerdrServer;
  darwinReconciliation = darwinConfiguration.home.activation.reconcileHerdrServer;
  linuxEnvironment = lib.toList linuxService.Service.Environment;
in
{
  domain-terminal-herdr-server-is-owned-by-a-linux-user-service =
    mkEvalCheck "domain-terminal-herdr-server-is-owned-by-a-linux-user-service"
      (
        lib.hasSuffix "/bin/herdr-server" (toString linuxService.Service.ExecStart)
        && linuxService.Service.Restart == "always"
        && linuxService.Service.MemoryHigh == "8G"
        && linuxService.Service.Delegate
        && linuxService.Service.NotifyAccess == "all"
        && builtins.elem "default.target" linuxService.Install.WantedBy
        && !(linuxService.Unit.X-RestartIfChanged or true)
        && !(linuxService.Unit.X-StopIfChanged or true)
        && lib.hasInfix "HERDR_RECONCILER=" linuxAdoption.data
      )
      "herdr.service must independently own the shared server lifecycle and memory backstop while activation adopts the live legacy server and its panes without stopping them";

  domain-terminal-herdr-server-reconciles-linux-build-changes =
    mkEvalCheck "domain-terminal-herdr-server-reconciles-linux-build-changes"
      (
        builtins.elem "adoptLegacyHerdrServer" linuxReconciliation.after
        && builtins.elem "reloadHerdrAfterConfigSeed" linuxReconciliation.after
        && lib.hasInfix "/bin/reconcile-herdr-server reconcile" linuxReconciliation.data
      )
      "Linux activation must live-handoff a running Herdr server after service migration and config seeding";

  domain-terminal-herdr-server-linux-path-reaches-the-user-profile =
    mkEvalCheck "domain-terminal-herdr-server-linux-path-reaches-the-user-profile"
      (builtins.any (lib.hasInfix "/etc/profiles/per-user/test/bin") linuxEnvironment)
      "herdr.service must give every pane the stable user-profile PATH so custom commands such as lazygit and nvim remain executable across profile rebuilds";

  domain-terminal-herdr-server-running-predicate-selects-only-default =
    pkgs.runCommandLocal "check-domain-terminal-herdr-server-running-predicate-selects-only-default"
      { nativeBuildInputs = [ pkgs.jq ]; }
      ''
        if echo '{"sessions":[{"default":false,"running":true}]}' \
          | jq -e -f ${../scripts/default-server-running.jq} >/dev/null; then
          exit 1
        fi
        echo '{"sessions":[{"default":true,"running":true}]}' \
          | jq -e -f ${../scripts/default-server-running.jq} >/dev/null
        touch "$out"
      '';

  domain-terminal-herdr-server-is-owned-by-a-darwin-launch-agent =
    mkEvalCheck "domain-terminal-herdr-server-is-owned-by-a-darwin-launch-agent"
      (
        darwinAgent.enable
        && lib.hasSuffix "/bin/herdr-rebuild-safe-launcher" darwinAgentProgram
        && !(lib.hasPrefix "/nix/store/" darwinAgentProgram)
        && builtins.elem "writeBoundary" darwinAgentPreservation.after
        && builtins.elem "setupLaunchAgents" darwinAgentPreservation.before
        && darwinAgent.config.RunAtLoad
        && darwinAgent.config.KeepAlive
        && lib.hasInfix "/etc/profiles/per-user/test/bin" darwinAgent.config.EnvironmentVariables.PATH
      )
      "the shared herdr server must use the rebuild-safe LaunchAgent constructor so profile changes cannot unload it";

  domain-terminal-herdr-server-reconciles-darwin-build-changes =
    mkEvalCheck "domain-terminal-herdr-server-reconciles-darwin-build-changes"
      (
        builtins.elem "setupLaunchAgents" darwinReconciliation.after
        && builtins.elem "reloadHerdrAfterConfigSeed" darwinReconciliation.after
        && lib.hasInfix "/bin/reconcile-herdr-server reconcile" darwinReconciliation.data
      )
      "Darwin activation must live-handoff a running Herdr server after LaunchAgent and config activation";
}
