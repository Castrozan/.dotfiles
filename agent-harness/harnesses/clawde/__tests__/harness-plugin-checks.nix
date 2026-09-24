{
  pkgs,
  mkEvalCheck,
  cfgWithBothHarnesses,
}:
{
  clawde-machine-tier-registers-the-complete-plugin =
    mkEvalCheck "clawde-machine-tier-registers-the-complete-plugin"
      (
        toString cfgWithBothHarnesses.home.file.".local/share/agent-plugins/dotfiles".source
        == toString cfgWithBothHarnesses.agentPlugins.bundle
        && pkgs.lib.hasInfix "plugin install dotfiles@dotagents" cfgWithBothHarnesses.home.activation.installProductionClaudePlugin.data
        && !(builtins.hasAttr ".claude/skills/research" cfgWithBothHarnesses.home.file)
      )
      "Claude agents must receive the complete registered production plugin through the shared user profile without a duplicate global research skill projection";

  clawde-steward-payload-is-not-in-the-machine-tier =
    mkEvalCheck "clawde-steward-payload-is-not-in-the-machine-tier"
      (!(builtins.hasAttr ".claude/skills/steward" cfgWithBothHarnesses.home.file))
      "the privileged steward payload must not sit in the machine tier every session loads; it belongs to the steward agent type and is scoped to the steward instance";
}
