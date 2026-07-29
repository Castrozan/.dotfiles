{
  mkEvalCheck,
  helpers,
  self,
}:
let
  cfgWithBothHarnesses = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    self.homeManagerModules.codex
    {
      clawde.agents = {
        agent-on-claude = {
          harness = "claude";
          personality = "Claude harness agent";
        };
        agent-on-codex = {
          harness = "codex";
          personality = "Codex harness agent";
        };
      };
    }
  ];

  harnesses = cfgWithBothHarnesses.clawde.harnesses;

  codexLaunchCommand = harnesses.codex.buildLaunchCommandFor {
    name = "agent-on-codex";
    agent = cfgWithBothHarnesses.clawde.agents.agent-on-codex;
    workspaceDirectory = "/tmp/agent-on-codex";
    instructionsFile = "/tmp/agent-on-codex/instructions.md";
    sessionArgvShellExpansion = "\${CLAWDE_SESSION_ARGV:-}";
    channelLaunchFlags = "";
  };
in
{
  clawde-claude-harness-package-is-injected =
    mkEvalCheck "clawde-claude-harness-package-is-injected" (harnesses.claude.package != null)
      "clawde pins no harness itself, so home/base/clawde/harnesses.nix must inject the claude package; a null package fails a clawde assertion the moment any agent runs on claude";

  clawde-codex-harness-package-is-injected =
    mkEvalCheck "clawde-codex-harness-package-is-injected" (harnesses.codex.package != null)
      "codex agents need clawde.harnesses.codex.package set from home/base/clawde/harnesses.nix, otherwise every codex agent fails a build-time assertion";

  clawde-codex-harness-launches-the-unwrapped-binary =
    mkEvalCheck "clawde-codex-harness-launches-the-unwrapped-binary"
      (harnesses.codex.package == cfgWithBothHarnesses.codex.unwrappedPackage)
      "clawde must launch the bare codex binary, not the interactive on-PATH wrapper: that wrapper already injects --model/--sandbox/--ask-for-approval/--no-alt-screen plus the human's own developer_instructions, and re-passing any of them makes codex exit 2";

  clawde-codex-agent-gets-its-own-harness-home =
    mkEvalCheck "clawde-codex-agent-gets-its-own-harness-home"
      (builtins.match ".*CODEX_HOME=.*harness-home/codex/agent-on-codex.*" codexLaunchCommand != null)
      "each codex agent must launch under its own CODEX_HOME so its workspace trust, MCP set and session history stay isolated from the human's ~/.codex and from every peer agent";

  clawde-codex-agent-config-is-materialized =
    mkEvalCheck "clawde-codex-agent-config-is-materialized"
      (builtins.hasAttr "clawde/harness-home/codex/agent-on-codex/config.toml" cfgWithBothHarnesses.home.file)
      "the per-agent CODEX_HOME needs a nix-generated config.toml; without it codex raises the directory-trust modal on launch and shows no run-state marker, so the heartbeat driver can never tell an idle pane from a working one";

  clawde-discord-channel-is-refused-on-codex =
    mkEvalCheck "clawde-discord-channel-is-refused-on-codex"
      (!(builtins.elem "discord" harnesses.codex.supportedChannelTypes))
      "codex has no --channels flag and no plugin providing an inbound channel transport, so pairing a discord channel with it must fail the build instead of launching an agent that can never receive a message";
}
