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
        && builtins.elem "default.target" linuxService.Install.WantedBy
        && !(linuxService.Unit.X-RestartIfChanged or true)
        && !(linuxService.Unit.X-StopIfChanged or true)
        && builtins.hasAttr "adoptLegacyHerdrServer" linuxConfiguration.home.activation
      )
      "herdr.service must independently own the shared server lifecycle and memory backstop while activation adopts the live legacy server and its panes without stopping them";

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
        && lib.hasSuffix "/bin/herdr-server" (builtins.head darwinAgent.config.ProgramArguments)
        && darwinAgent.config.RunAtLoad
        && darwinAgent.config.KeepAlive
        && lib.hasInfix "/etc/profiles/per-user/test/bin" darwinAgent.config.EnvironmentVariables.PATH
      )
      "the shared herdr server must have the same independent launchd ownership and user-profile PATH on darwin";
}
