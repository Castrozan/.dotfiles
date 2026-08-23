_:
let
  coreAgentRules = builtins.readFile ../../../agent-harness/agent-instructions/core-rules/core.md;
in
{
  home.file = {
    ".dotfiles/machine-configuration/editors/cursor/cursor-global-user-rules.md".source =
      ../../../agent-harness/agent-instructions/core-rules/core.md;
    ".dotfiles/.cursor/rules/core.mdc".text = ''
      ---
      description: Core agent behavior instructions
      alwaysApply: true
      ---

      ${coreAgentRules}
    '';
  };
}
