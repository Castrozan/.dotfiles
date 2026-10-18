{ pkgs }:
let
  wellputSource = import ../../agent-instructions/wellput-plugin/upstream.nix { inherit pkgs; };
  projection = import ../../agent-instructions/instruction-projection.nix { inherit pkgs; };
in
projection.instructionFile {
  name = "hermes-interactive-instructions.md";
  sources = [
    ../../agent-instructions/interactive-communication.md
    "${wellputSource}/skills/wellput/references/interactive-communication.md"
  ];
  deployed = "/.hermes/config.yaml";
  destinations =
    (projection.interactiveDestinations {
      coreInstructionFile = "/.hermes/SOUL.md";
    })
    // {
      "${builtins.unsafeDiscardStringContext "${wellputSource}/skills/wellput"}" =
        "/.hermes/plugins/dotfiles/skills/wellput";
    };
}
