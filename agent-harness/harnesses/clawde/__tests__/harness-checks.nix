{
  pkgs,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fixtures = import ./harness-check-fixtures.nix { inherit helpers self; };
  inherit (fixtures) bothHarnessModules cfgWithBothHarnesses parseDeployedJson;

  harnessNamesCarryingDiscord = builtins.sort (a: b: a < b) (
    builtins.attrNames (
      pkgs.lib.filterAttrs (_: harness: builtins.elem "discord" harness.supportedChannelTypes) harnesses
    )
  );

  eligibleHarnessesOf =
    agentName:
    (parseDeployedJson cfgWithBothHarnesses.home.file."clawde/launch-config/${agentName}.json".text)
    .harness_launch_commands;

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
      "clawde pins no harness itself, so agent-harness/harnesses/clawde/harnesses.nix must inject the claude package; a null package fails a clawde assertion the moment any agent runs on claude";

  clawde-codex-harness-package-is-injected =
    mkEvalCheck "clawde-codex-harness-package-is-injected" (harnesses.codex.package != null)
      "codex agents need clawde.harnesses.codex.package set from agent-harness/harnesses/clawde/harnesses.nix, otherwise every codex agent fails a build-time assertion";

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
        builtins.hasAttr ".local/share/claude-skill-sets/harness-check-set/.claude/skills/research" cfgWithBothHarnesses.home.file
        && !(cfgWithBothHarnesses.home.file.".local/share/claude-skill-sets/harness-check-set/.claude/skills/research".recursive
          or false
        )
      )
      "a skill set must materialize as one symlink per skill directory, never recursive: recursive makes home-manager build a real directory whose SKILL.md is itself a symlink, and codex silently skips every such skill, so a codex agent loads none of its declared skills while the directory listing looks complete; the hasAttr half keeps this from passing vacuously when no set materializes at all";

  clawde-the-normal-harness-set-carries-every-interactive-skill =
    mkEvalCheck "clawde-the-normal-harness-set-carries-every-interactive-skill"
      (builtins.all
        (
          skillName:
          builtins.hasAttr ".local/share/claude-skill-sets/normal-harness/.claude/skills/${skillName}" cfgWithBothHarnesses.home.file
        )
        (import
          ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
          { hostname = "test"; }
        ).defaultInteractiveSkillNames
      )
      "an agent naming normalHarnessSkillSetDirectory is asking for what a keyboard session carries, so that set must hold the curated interactive list: materialized short, the agent silently runs a harness switch onto codex or opencode missing exactly the skills its job assumes";

  clawde-every-installed-harness-is-switchable-at-runtime =
    mkEvalCheck "clawde-every-installed-harness-is-switchable-at-runtime"
      (
        builtins.attrNames (eligibleHarnessesOf "agent-on-codex") == [
          "claude"
          "codex"
          "opencode"
        ]
      )
      "`clawde harness <agent> <harness>` can only move an agent onto a harness the deployment already materialized a launch command for, so a channel-free agent must carry one per installed harness: drop one and the switch silently refuses a harness the machine can actually run";

  clawde-a-channel-agent-cannot-be-switched-onto-a-harness-without-that-channel =
    mkEvalCheck "clawde-a-channel-agent-cannot-be-switched-onto-a-harness-without-that-channel"
      (builtins.attrNames (eligibleHarnessesOf "agent-on-discord") == harnessNamesCarryingDiscord)
      "the runtime harness switch bypasses the build-time channel assertion, so the eligible set is the only thing standing between a discord agent and a harness that cannot receive a message: it must be exactly the harnesses declaring that channel, so a harness added without discord support stays unreachable by `clawde harness`";

  clawde-model-by-harness-pins-what-an-agent-runs-after-a-switch =
    mkEvalCheck "clawde-model-by-harness-pins-what-an-agent-runs-after-a-switch"
      (
        (parseDeployedJson
          cfgWithBothHarnesses.home.file."clawde/harness-home/opencode/agent-on-codex/opencode.json".text
        ).model == "opencode/some-free-model"
      )
      "a model identifier from one harness is meaningless to another, so switching harnesses must resolve the model again through modelByHarness rather than carrying the declared harness's model across";

  clawde-no-launch-command-can-be-rewritten-by-a-shell-alias =
    mkEvalCheck "clawde-no-launch-command-can-be-rewritten-by-a-shell-alias"
      (builtins.all (invocationIsAliasProof: invocationIsAliasProof) (
        pkgs.lib.mapAttrsToList (
          harnessName: launchCommand:
          pkgs.lib.hasInfix " command ${harnesses.${harnessName}.binaryName} " " ${launchCommand} "
        ) (eligibleHarnessesOf "agent-on-codex")
      ))
      "this machine exports BASH_ENV pointing at an alias file that turns on expand_aliases and aliases claude to a wrapper passing --append-system-prompt-file, and a launch command runs through exactly such a shell: without the command builtin in front of the binary the alias wins over PATH, the wrapper's flags collide with the ones clawde built, and the agent dies at argument parsing on every restart forever";

  clawde-no-launch-command-resolves-its-binary-through-the-ambient-path =
    mkEvalCheck "clawde-no-launch-command-resolves-its-binary-through-the-ambient-path"
      (builtins.all (resolvesOnlyThroughItsOwnDirectory: resolvesOnlyThroughItsOwnDirectory) (
        pkgs.lib.mapAttrsToList (
          harnessName: launchCommand:
          pkgs.lib.hasInfix "PATH=${cfgWithBothHarnesses.home.homeDirectory}/clawde/harness-home/${harnessName}/bin:\"$PATH\" " launchCommand
        ) (eligibleHarnessesOf "agent-on-codex")
      ))
      "the command builtin defeats the alias but still resolves the name through whatever PATH the pane inherits, so any stale binary sitting earlier on PATH quietly replaces the one the deployment pinned: a claude 2.1.72 left behind in /opt/homebrew/bin did exactly that and killed an agent at argument parsing every 300 seconds for two days while the configured 2.1.220 sat unused. Every launch command must therefore prepend its own harness-home binary directory, which holds nothing but the package this deployment built";
}
