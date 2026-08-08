{ pkgs, ... }:
let
  memoryScripts = ./scripts;
  appendAgentMemoryFact = pkgs.writeShellScriptBin "clawde-agent-memory-append" ''
    exec ${pkgs.python312}/bin/python3 ${memoryScripts}/append_agent_memory_fact.py "$@"
  '';
in
{
  home.packages = [ appendAgentMemoryFact ];
}
