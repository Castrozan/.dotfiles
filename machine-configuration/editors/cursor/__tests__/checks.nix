{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  cursorRuleFiles = (import ../cursor-agent-rules-home-manager.nix { }).home.file;
  coreAgentRules = builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/core.md;
  cursorCoreRule = cursorRuleFiles.".dotfiles/.cursor/rules/core.mdc".text or "";
  expectedCursorCoreRule = ''
    ---
    description: Core agent behavior instructions
    alwaysApply: true
    ---

    ${coreAgentRules}
  '';
in
{
  domain-cursor-keeps-rule-metadata-at-the-cursor-boundary =
    mkEvalCheck "domain-cursor-keeps-rule-metadata-at-the-cursor-boundary"
      (
        builtins.hasAttr ".dotfiles/.cursor/rules/core.mdc" cursorRuleFiles
        && !(builtins.hasAttr ".dotfiles/.cursor/core.md" cursorRuleFiles)
        && cursorCoreRule == expectedCursorCoreRule
        &&
          builtins.readFile
            cursorRuleFiles.".dotfiles/machine-configuration/editors/cursor/cursor-global-user-rules.md".source
          == coreAgentRules
      )
      "Cursor must own its recognized .cursor/rules/*.mdc metadata while the canonical core and exported user rules stay plain";
}
