{
  pkgs,
  lib,
  hostname ? "",
  ...
}:
let
  provenanceScripts = ./scripts;
  agentSessionScripts = ../../../../agent-harness/session-control;
  runtimePath = lib.makeBinPath (
    [ pkgs.git ]
    ++ lib.optionals pkgs.stdenv.isLinux [ pkgs.procps ]
    ++ lib.optionals pkgs.stdenv.isDarwin [ pkgs.lsof ]
  );
  runtimeEnvironment = ''
    export PATH="${runtimePath}:$PATH"
    export PYTHONPATH="${provenanceScripts}:${agentSessionScripts}"
    export AGENT_COMMIT_PROVENANCE_MACHINE="${hostname}"
  '';
  recordAgentCommitProvenanceTrailers = pkgs.writeShellScript "prepare-commit-msg" ''
    ${runtimeEnvironment}
    exec ${pkgs.python312}/bin/python3 ${provenanceScripts}/record_agent_commit_provenance_trailers.py "$@"
  '';
  showAgentCommitProvenance = pkgs.writeShellScriptBin "git-agent-session" ''
    ${runtimeEnvironment}
    exec ${pkgs.python312}/bin/python3 ${provenanceScripts}/show_agent_commit_provenance.py "$@"
  '';
in
{
  home.packages = [ showAgentCommitProvenance ];

  home.file.".githooks/prepare-commit-msg" = {
    source = recordAgentCommitProvenanceTrailers;
    executable = true;
  };
}
