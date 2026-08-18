{ config, pkgs, ... }:
let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.pyyaml
  ]);

  # The interactive wrapper appends the always-on reply-shape surface unconditionally, so a subject launched
  # through it carries that surface even under `-p --system-prompt` with the isolation variables stripped. Every
  # sample then measures the live machine instead of the git-controlled instruction paths the suite declares.
  agent-eval = pkgs.writeShellScriptBin "agent-eval" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pythonEnv
        config.claude.unwrappedPackage
      ]
    }:$PATH"
    exec ${pythonEnv}/bin/python3 ~/.dotfiles/agent-harness/quality/evaluations/run-evals.py "$@"
  '';

  agent-e2e = pkgs.writeShellScriptBin "agent-e2e" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pythonEnv
        pkgs.git
      ]
    }:$PATH"
    exec ${pythonEnv}/bin/python3 ~/.dotfiles/agent-harness/quality/evaluations/e2e/run-e2e-tests.py "$@"
  '';
in
{
  home.packages = [
    agent-eval
    agent-e2e
  ];
}
