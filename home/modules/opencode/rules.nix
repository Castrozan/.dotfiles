_:
let
  opencodeRules = ''
    # OpenCode Project Context

    ${builtins.readFile ../../../agents/core.md}
  '';
in
{
  home.file.".dotfiles/AGENTS.md".text = opencodeRules;
}
