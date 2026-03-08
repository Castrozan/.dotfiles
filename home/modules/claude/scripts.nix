{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "claude-exit" ''
      export PATH="${pkgs.procps}/bin:$PATH"
      ${builtins.readFile ./scripts/claude-exit}
    '')
  ];
}
