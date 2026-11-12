{ pkgs, inputs, ... }:
let
  agentEvals = inputs.agent-evals.packages.${pkgs.stdenv.hostPlatform.system}.default;
  policyPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.pyyaml ]);
  repositoryScope = pkgs.writeTextDir "dotfiles_repository_scope.py" (
    builtins.readFile ../../hooks/runtime/common/personal-tooling/dotfiles_repository_scope.py
  );
  guardedAgentEvals = pkgs.writeShellScriptBin "agent-evals" ''
    export PYTHONPATH=${repositoryScope}
    exec ${policyPython}/bin/python3 ${./scripts/codex_only_evaluations.py} ${pkgs.lib.getExe agentEvals} "$@"
  '';
  dotfilesEvals = pkgs.writeShellScriptBin "dotfiles-evals" ''
    export AGENT_EVALS_CONFIG=agent-harness/quality/evaluations/config.yaml
    exec ${guardedAgentEvals}/bin/agent-evals "$@"
  '';
in
{
  home.packages = [
    guardedAgentEvals
    dotfilesEvals
  ];
}
