{ pkgs, ... }:
let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.pyyaml
  ]);

  agent-eval = pkgs.writeShellScriptBin "agent-eval" ''
    export PATH="${pkgs.lib.makeBinPath [ pythonEnv ]}:$PATH"
    exec ${pythonEnv}/bin/python3 ~/.dotfiles/agents/evals/run-evals.py "$@"
  '';

  agent-e2e = pkgs.writeShellScriptBin "agent-e2e" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pythonEnv
        pkgs.tmux
        pkgs.git
      ]
    }:$PATH"
    exec ${pythonEnv}/bin/python3 ~/.dotfiles/agents/evals/e2e/run-e2e-tests.py "$@"
  '';
in
{
  home.packages = [
    agent-eval
    agent-e2e
  ];
}
