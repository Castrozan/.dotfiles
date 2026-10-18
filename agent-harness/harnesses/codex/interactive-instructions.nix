{ pkgs, homeDirectory }:
let
  projection = import ../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "codex-interactive-session-only-developer-instructions.md";
  sources = [
    ../../agent-instructions/interactive-communication.md
    ../../../agent-harness/agent-instructions/core-rules/servant-identity.md
    ./session-title-instructions.md
  ];
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "${homeDirectory}/.codex/AGENTS.md";
  };
}
