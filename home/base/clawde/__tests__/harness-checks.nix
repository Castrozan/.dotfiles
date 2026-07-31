{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
}:
let
  bothHarnessModules = [
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

  cfgWithBothHarnesses = helpers.homeManagerTestConfiguration bothHarnessModules;

  cfgWithStandaloneClawde = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
  ];

  cfgOnTheEvaluatingSystem = helpers.homeManagerTestConfigurationForEvaluatingSystem bothHarnessModules;

  harnessActivationScriptForOneCodexAgent =
    extraAgentSettings:
    (helpers.homeManagerTestConfiguration [
      self.homeManagerModules.clawde
      self.homeManagerModules.claude-code
      self.homeManagerModules.codex
      {
        clawde.agents.lone-codex-agent = {
          harness = "codex";
          personality = "Codex harness agent";
        }
        // extraAgentSettings;
      }
    ]).home.activation.runHarnessAgentActivations.data;

  inherit (cfgWithBothHarnesses.clawde) harnesses;

  codexLaunchCommand = harnesses.codex.buildLaunchCommandFor {
    name = "agent-on-codex";
    agent = cfgWithBothHarnesses.clawde.agents.agent-on-codex;
    workspaceDirectory = "/tmp/agent-on-codex";
    instructionsFile = "/tmp/agent-on-codex/instructions.md";
    sessionArgvShellExpansion = "\${CLAWDE_SESSION_ARGV:-}";
    channelLaunchFlags = "";
  };
  codexAgentConfigurationFile =
    cfgOnTheEvaluatingSystem.home.file."clawde/harness-home/codex/agent-on-codex/config.toml".source;
in
{
  clawde-standalone-module-evaluates-without-harness-packages =
    mkEvalCheck "clawde-standalone-module-evaluates-without-harness-packages"
      (
        cfgWithStandaloneClawde.clawde.harnesses.claude.package == null
        && cfgWithStandaloneClawde.clawde.harnesses.codex.package == null
      )
      "the exported clawde module must evaluate without the claude-code and codex modules when no agents require either harness";

  clawde-machine-tier-carries-the-research-skill =
    mkEvalCheck "clawde-machine-tier-carries-the-research-skill"
      (builtins.hasAttr ".claude/skills/research" cfgWithBothHarnesses.home.file)
      "every clawde agent on the claude harness takes its skills from the machine tier at .claude/skills rather than a per-agent --add-dir set; an empty machine tier leaves those agents with no skills at all";

  clawde-steward-payload-is-not-in-the-machine-tier =
    mkEvalCheck "clawde-steward-payload-is-not-in-the-machine-tier"
      (!(builtins.hasAttr ".claude/skills/steward" cfgWithBothHarnesses.home.file))
      "the privileged steward payload must not sit in the machine tier every session loads; it belongs to the steward agent type and is scoped to the steward instance";

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
    pkgs.runCommandLocal "check-clawde-codex-agent-config-is-materialized" { }
      ''
        grep -q 'trust_level = "trusted"' ${codexAgentConfigurationFile}
        grep -q 'run-state' ${codexAgentConfigurationFile}
        touch $out
      '';

  clawde-codex-activation-seeds-the-agent-type-skill-directories =
    mkEvalCheck "clawde-codex-activation-seeds-the-agent-type-skill-directories"
      (
        harnessActivationScriptForOneCodexAgent { type = "steward"; }
        != harnessActivationScriptForOneCodexAgent { }
      )
      "the codex harness seeds an agent's skills at activation time, so that activation must run against the effective agent: reading the raw clawde.agents entry drops every skill directory an agent type contributes and the agent launches with an empty skills directory while nothing else looks wrong";

  clawde-skill-sets-materialize-as-directory-symlinks =
    mkEvalCheck "clawde-skill-sets-materialize-as-directory-symlinks"
      (
        !(cfgWithBothHarnesses.home.file.".local/share/claude-skill-sets/personal/.claude/skills/research".recursive
          or false
        )
      )
      "a skill set must materialize as one symlink per skill directory, never recursive: recursive makes home-manager build a real directory whose SKILL.md is itself a symlink, and codex silently skips every such skill, so a codex agent loads none of its declared skills while the directory listing looks complete";

  clawde-discord-channel-is-refused-on-codex =
    mkEvalCheck "clawde-discord-channel-is-refused-on-codex"
      (!(builtins.elem "discord" harnesses.codex.supportedChannelTypes))
      "codex has no --channels flag and no plugin providing an inbound channel transport, so pairing a discord channel with it must fail the build instead of launching an agent that can never receive a message";
}
