{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "claude-exit" ''
      export PATH="${pkgs.procps}/bin:$PATH"
      ${builtins.readFile ./scripts/claude-exit}
    '')
    (pkgs.writeShellScriptBin "claude-restart" ''
      export PATH="${pkgs.procps}/bin:${pkgs.tmux}/bin:$PATH"
      ${builtins.readFile ./scripts/claude-restart}
    '')
  ];
}
