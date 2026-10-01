{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  linuxConfiguration = helpers.homeManagerTestConfiguration [ ../herdr-home-manager.nix ];
  darwinConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../herdr-home-manager.nix
    ../../../../../agent-harness/harnesses/hermes
  ];
  linuxService = linuxConfiguration.systemd.user.services.herdr;
  darwinAgent = darwinConfiguration.launchd.agents.herdr;
  darwinAgentProgram = builtins.head darwinAgent.config.ProgramArguments;
  darwinAgentPreservation = darwinConfiguration.home.activation."preserveRunningLaunchAgent-herdr";
  linuxAdoption = linuxConfiguration.home.activation.adoptLegacyHerdrServer;
  linuxEnvironment = lib.toList linuxService.Service.Environment;
  integrationRefreshes =
    map (configuration: configuration.home.activation.refreshHerdrAgentIntegrations)
      [
        linuxConfiguration
        darwinConfiguration
      ];
  runningPackageRetentions =
    map (configuration: configuration.home.activation.retainRunningHerdrPackage)
      [
        linuxConfiguration
        darwinConfiguration
      ];
in
{
  domain-terminal-herdr-agent-resume = import ../herdr-agent-resume-package.nix {
    inherit pkgs lib;
  };

  domain-terminal-herdr-server-is-owned-by-a-linux-user-service =
    mkEvalCheck "domain-terminal-herdr-server-is-owned-by-a-linux-user-service"
      (
        lib.hasSuffix "/bin/herdr-server" (toString linuxService.Service.ExecStart)
        && linuxService.Service.Restart == "always"
        && linuxService.Service.MemoryHigh == "8G"
        && linuxService.Service.Delegate
        && builtins.elem "default.target" linuxService.Install.WantedBy
        && !(linuxService.Unit.X-RestartIfChanged or true)
        && !(linuxService.Unit.X-StopIfChanged or true)
        && builtins.elem "reloadSystemd" linuxAdoption.after
      )
      "herdr.service must independently own the shared server lifecycle and memory backstop while activation adopts the live legacy server and its panes without stopping them";

  domain-terminal-herdr-rebuild-preserves-the-running-server =
    mkEvalCheck "domain-terminal-herdr-rebuild-preserves-the-running-server"
      (builtins.all (configuration: !(configuration.home.activation ? reconcileHerdrServer)) [
        linuxConfiguration
        darwinConfiguration
      ])
      "rebuild must not automatically replace the shared Herdr server and disconnect attached clients";

  domain-terminal-herdr-rebuild-retains-the-running-server-package =
    mkEvalCheck "domain-terminal-herdr-rebuild-retains-the-running-server-package"
      (builtins.all (
        retention:
        builtins.elem "writeBoundary" retention.after
        && lib.hasInfix "select-herdr-client retain-running" retention.data
      ) runningPackageRetentions)
      "rebuild must retain the exact package of the socket-owning Herdr server so compatible server commands remain available after profile changes";

  domain-terminal-herdr-rebuild-still-reloads-seeded-config =
    mkEvalCheck "domain-terminal-herdr-rebuild-still-reloads-seeded-config"
      (builtins.all
        (
          configuration:
          let
            reload = configuration.home.activation.reloadHerdrAfterConfigSeed;
          in
          builtins.elem "seedHerdrConfigAsMutableFile" reload.after
          && lib.hasInfix "herdr server reload-config" reload.data
        )
        [
          linuxConfiguration
          darwinConfiguration
        ]
      )
      "rebuild must continue to reload seeded Herdr configuration without replacing the server";

  domain-terminal-herdr-rebuild-refreshes-agent-integrations-after-config =
    mkEvalCheck "domain-terminal-herdr-rebuild-refreshes-agent-integrations-after-config"
      (builtins.all (
        refresh:
        builtins.elem "linkGeneration" refresh.after
        && builtins.elem "seedCodexConfigAsMutableFile" refresh.after
        && lib.hasInfix "/bin/herdr integration install codex" refresh.data
        && !(lib.hasInfix "/bin/herdr integration install opencode" refresh.data)
      ) integrationRefreshes)
      "rebuild must refresh the mutable Codex integration without writing immutable OpenCode terminal configuration";

  domain-terminal-herdr-deploys-native-opencode-terminal-plugin =
    mkEvalCheck "domain-terminal-herdr-deploys-native-opencode-terminal-plugin"
      (builtins.all (configuration: configuration.home.file ? ".config/opencode/herdr-session") [
        linuxConfiguration
        darwinConfiguration
      ])
      "Herdr's existing V2 terminal integration must deploy declaratively on Linux and Darwin";

  domain-terminal-herdr-refreshes-hermes-only-when-configured =
    mkEvalCheck "domain-terminal-herdr-refreshes-hermes-only-when-configured"
      (
        lib.hasInfix "/bin/herdr integration install hermes" darwinConfiguration.home.activation.refreshHerdrAgentIntegrations.data
        && !(lib.hasInfix "/bin/herdr integration install hermes" linuxConfiguration.home.activation.refreshHerdrAgentIntegrations.data)
      )
      "Herdr must install the Hermes integration only on hosts whose Home Manager configuration includes Hermes";

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
}
