{ pkgs }:
let
  projection = import ../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "hermes-interactive-instructions.md";
  sources = [
    ../../agent-instructions/skills/writing/humanize/references/interactive-communication.md
  ];
  deployed = "/.hermes/config.yaml";
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "/.hermes/SOUL.md";
    humanizeSkillDirectory = "/.hermes/skills/humanize";
  };
}
