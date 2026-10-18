{ pkgs, homeDirectory }:
let
  projection = import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "claude-interactive-session-only-system-prompt-surfaces.md";
  sources = [
    ./interactive-tool-usage.md
    ../../../agent-instructions/interactive-communication.md
    ../../../agent-instructions/core-rules/adaptive-implementation-delivery-process.md
    ../../../agent-instructions/core-rules/servant-identity.md
  ];
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "${homeDirectory}/.local/share/agent-plugins/dotfiles/plugin/skills/core/SKILL.md";
  };
}
