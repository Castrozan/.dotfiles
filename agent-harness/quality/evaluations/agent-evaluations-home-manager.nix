{ config, pkgs, ... }:
let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.pyyaml
  ]);

  nodeProviderRuntime = pkgs.callPackage ./node-provider-runtime-package.nix {
    nodejs = pkgs.nodejs_22;
  };

  # The interactive wrapper appends the always-on reply-shape surface unconditionally, so an SDK-launched subject
  # that resolves it measures the live machine instead of the git-controlled instruction paths the suite declares.
  agent-eval = pkgs.writeShellScriptBin "agent-eval" ''
    export AGENT_EVAL_CLAUDE_BINARY="${pkgs.lib.getExe config.claude.unwrappedPackage}"
    export AGENT_EVAL_CODEX_BINARY="${pkgs.lib.getExe config.codex.unwrappedPackage}"
    export PATH="${
      pkgs.lib.makeBinPath [
        pythonEnv
        nodeProviderRuntime
        config.claude.unwrappedPackage
        config.codex.unwrappedPackage
        config.opencode.unwrappedPackage
      ]
    }:$PATH"
    exec ${pythonEnv}/bin/python3 ~/.dotfiles/agent-harness/quality/evaluations/run-evals.py "$@"
  '';

  # End-to-end scenarios score the deployed session, so PATH keeps the interactive wrapper for the herdr-driven
  # subject. Only the compliance judge is pinned to the unwrapped binary, because a judge that inherits the
  # reply-shape surface grades against instructions it was never given.
  agent-e2e = pkgs.writeShellScriptBin "agent-e2e" ''
    export AGENT_EVAL_CLAUDE_BINARY="${pkgs.lib.getExe config.claude.unwrappedPackage}"
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
