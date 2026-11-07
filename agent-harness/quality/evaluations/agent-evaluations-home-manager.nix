{ pkgs, inputs, ... }:
let
  agentEvals = inputs.agent-evals.packages.${pkgs.stdenv.hostPlatform.system}.default;
  dotfilesEvals = pkgs.writeShellScriptBin "dotfiles-evals" ''
    export AGENT_EVALS_CONFIG=agent-harness/quality/evaluations/config.yaml
    exec ${pkgs.lib.getExe agentEvals} "$@"
  '';
in
{
  home.packages = [
    agentEvals
    dotfilesEvals
  ];
}
