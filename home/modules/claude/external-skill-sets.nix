{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config.home) homeDirectory;
  skillSetsBaseDirectory = "${homeDirectory}/.local/share/claude-skill-sets";
  personalSkillSetDirectory = "${skillSetsBaseDirectory}/personal";
  claudeConfigurationDirectory = "${homeDirectory}/.claude";
  claudeCoreInstructionsFile = "${homeDirectory}/.dotfiles/agents/core.md";

  defaultClaudeFishFunction = ''
    function claude --description "Claude Code with workspace skills"
      command claude-workspace $argv
    end
  '';

  claudeWorkspaceScript = pkgs.writeShellScriptBin "claude-workspace" ''
    export CLAUDE_BINARY_PATH="${lib.getExe config.claude.package}"
    export CLAUDE_CORE_INSTRUCTIONS_FILE="${claudeCoreInstructionsFile}"
    export CLAUDE_GLOBAL_CONFIG_DIRECTORY="${claudeConfigurationDirectory}"
    export CLAUDE_GLOBAL_STATE_FILE="${homeDirectory}/.claude.json"
    export CLAUDE_PERSONAL_SKILL_SET_DIRECTORY="${personalSkillSetDirectory}"
    exec ${pkgs.python312}/bin/python3 ${./scripts/launch-claude-workspace-session} "$@"
  '';
in
{
  home.packages = [ claudeWorkspaceScript ];

  xdg.configFile."fish/conf.d/claude-skill-sets.fish".text = defaultClaudeFishFunction;
}
