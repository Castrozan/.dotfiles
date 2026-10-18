{ pkgs, homeDirectory }:
let
  projection = import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "opencode-interactive-session-only-instructions.md";
  sources = [
    ../../../agent-instructions/interactive-communication.md
    ../../../agent-instructions/core-rules/servant-identity.md
  ];
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "${homeDirectory}/.config/opencode/AGENTS.md";
  };
}
