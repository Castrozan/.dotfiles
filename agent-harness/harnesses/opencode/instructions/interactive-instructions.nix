{ pkgs, homeDirectory }:
let
  projection = import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "opencode-interactive-session-only-instructions.md";
  sources = [
    ../../../agent-instructions/skills/writing/humanize/references/interactive-communication.md
    ../../../agent-instructions/core-rules/servant-identity.md
  ];
  destinations = projection.interactiveDestinations {
    coreInstructionFile = "${homeDirectory}/.config/opencode/AGENTS.md";
    humanizeSkillDirectory = "${homeDirectory}/.local/share/agent-plugins/dotfiles/plugin/skills/humanize";
  };
}
