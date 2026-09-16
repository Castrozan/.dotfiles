{ pkgs }:
let
  projection = import ../../agent-instructions/instruction-projection.nix { inherit pkgs; };
  managedSkillDirectory =
    skillName:
    projection.skillDirectory {
      source = ../../agent-instructions/skills/writing + "/${skillName}";
      deployed = "/.hermes/skills/${skillName}";
      destinations = projection.interactiveDestinations {
        coreInstructionFile = "/.hermes/SOUL.md";
        humanizeSkillDirectory = "/.hermes/skills/humanize";
      };
    };

in
{
  humanize = "${managedSkillDirectory "humanize"}/SKILL.md";
  docs = "${managedSkillDirectory "docs"}/SKILL.md";
}
