{ pkgs, homeDirectory }:
let
  projection = import ../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "pi-interactive-session-only-reply-rules.md";
  sources = [
    ../../agent-instructions/skills/writing/humanize/references/interactive-communication.md
  ];
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "${homeDirectory}/.pi/agent/AGENTS.md";
    humanizeSkillDirectory = "${homeDirectory}/.local/share/agent-skill-index/humanize";
  };
}
