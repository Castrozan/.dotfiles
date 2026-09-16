{ pkgs, homeDirectory }:
let
  projection = import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "claude-interactive-session-only-system-prompt-surfaces.md";
  sources = [
    ../../../agent-instructions/skills/writing/humanize/references/interactive-communication.md
    ../../../agent-instructions/core-rules/adaptive-implementation-delivery-process.md
    ../../../agent-instructions/core-rules/servant-identity.md
  ];
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "${homeDirectory}/.claude/skills/core/SKILL.md";
    humanizeSkillDirectory = "${homeDirectory}/.claude/skills/humanize";
  };
}
