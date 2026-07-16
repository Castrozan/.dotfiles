{
  lib,
  mkEvalCheck,
}:
let
  partitionFor =
    allMcpServerNames:
    import ../mcps/mcp-server-injection-partition.nix { inherit lib allMcpServerNames; };

  representativeInteractiveDefinitionNames = [
    "chrome-devtools"
    "codex"
    "a2a"
    "mem0"
  ];

  partition = partitionFor representativeInteractiveDefinitionNames;
in
{
  a2a-kept-agent-only-and-never-retired =
    mkEvalCheck "a2a-kept-agent-only-and-never-retired"
      (
        builtins.elem "a2a" partition.agentOnlyMcpServerNames
        && !(builtins.elem "a2a" partition.retiredMcpServerNames)
      )
      "a2a must stay agent-only (kept in mcpServerDefinitions so buildClawdeAgentMcpConfigFile can scope it into the steward's per-agent config) and never retired; retiring it would break the steward's a2a wiring, and lib.getAttrs would throw at build";

  a2a-excluded-from-interactive-mcp-injection =
    mkEvalCheck "a2a-excluded-from-interactive-mcp-injection"
      (!(builtins.elem "a2a" partition.interactivelyInjectedMcpServerNames))
      "a2a must be excluded from the interactive ~/.claude.json injection; re-injecting it interactively regresses the documented token-usage-reduction goal with no other test to catch the change";

  retired-mcps-remain-in-managed-prune-set =
    mkEvalCheck "retired-mcps-remain-in-managed-prune-set"
      (lib.all (retiredName: builtins.elem retiredName partition.managedMcpServerNames) [
        "brave-devtools"
        "browser-use"
        "figma"
        "figma-read"
      ])
      "brave-devtools, browser-use, figma, and figma-read must stay in the managed prune set so the injector strips any prior entry from existing ~/.claude.json on every host that previously injected them; dropping one leaves a dead stdio MCP that spawns a server that never connects";

  mem0-remains-in-managed-prune-set-on-hosts-without-it =
    mkEvalCheck "mem0-remains-in-managed-prune-set-on-hosts-without-it"
      (
        let
          partitionWithoutMem0 = partitionFor [
            "chrome-devtools"
            "codex"
            "a2a"
          ];
        in
        builtins.elem "mem0" partitionWithoutMem0.managedMcpServerNames
      )
      "mem0 must stay in the managed prune set even on hosts whose mcpServerDefinitions omit it (no private mem0-host.nix), because mem0 is host-gated into the definitions; without the standalone hostGatedRemoteMemoryMcpServerNames entry a stale localhost mem0 sse entry written by a prior rebuild would never be pruned from ~/.claude.json and would persist as a dead server";
}
