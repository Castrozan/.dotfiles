{ pkgs, ... }:
let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.pyyaml
  ]);

  agent-eval = pkgs.writeShellScriptBin "agent-eval" ''
    export PATH="${pkgs.lib.makeBinPath [ pythonEnv ]}:$PATH"
    exec ${pythonEnv}/bin/python3 ~/.dotfiles/tests/agents/run-evals.py "$@"
  '';
in
{
  home.packages = [ agent-eval ];
}
