{ pkgs, lib }:
let
  projection = import ../instruction-projection.nix { inherit pkgs; };
  homeDirectory = "/home/instruction-fixture";
  moduleArguments = {
    inherit pkgs lib;
    hostname = "test";
    config.home.homeDirectory = homeDirectory;
  };
  moduleHomeFiles = map (module: (import module moduleArguments).home.file) [
    ../interactive-skill-catalog/interactive-skill-index-home-manager.nix
    ../dotfiles-checkout-agent-surfaces/dotfiles-repo-skills-home-manager.nix
    ../dotfiles-checkout-agent-surfaces/dotfiles-repo-agent-instructions-home-manager.nix
    ../../harnesses/claude-code/skills/global-skills-home-manager.nix
    ../../harnesses/claude-code/subagents/default.nix
    ../../harnesses/codex/skills.nix
    ../../harnesses/opencode/skills.nix
    ../../harnesses/opencode/agents/subagents.nix
    ../../harnesses/codex/global-instructions.nix
    ../../harnesses/opencode/instructions/global-instructions.nix
    ../../harnesses/pi/global-instructions.nix
  ];
  hermesSkills = import ../../harnesses/hermes/managed-skills.nix { inherit pkgs; };
  homeFileDefinitions = builtins.foldl' (all: files: all // files) {
    ".hermes/SOUL.md".source = import ../../harnesses/hermes/soul.nix { inherit pkgs; };
    ".hermes/skills/humanize".source = builtins.dirOf hermesSkills.humanize;
    ".hermes/skills/docs".source = builtins.dirOf hermesSkills.docs;
  } moduleHomeFiles;
  homeFiles = lib.mapAttrs (
    name: value: value.source or (pkgs.writeText (builtins.baseNameOf name) value.text)
  ) homeFileDefinitions;
  interactivePromptFiles =
    map
      (
        generator:
        let
          source = import generator { inherit pkgs homeDirectory; };
        in
        {
          inherit source;
          destination = toString source;
        }
      )
      [
        ../../harnesses/claude-code/launch/interactive-session-instructions.nix
        ../../harnesses/codex/interactive-instructions.nix
        ../../harnesses/opencode/instructions/interactive-instructions.nix
        ../../harnesses/pi/interactive-instructions.nix
      ];
  stewardPromptFiles =
    map
      (
        localWrapperRepoPath:
        let
          fragments = import ../../harnesses/clawde/agents/steward/instructions.nix {
            inherit lib localWrapperRepoPath;
            hostname = "test";
          };
          source = projection.instructionText {
            name = "steward-owned-instructions.md";
            text = fragments.machineLocalWrapperDirective + fragments.repoCiToolingDirective;
            deployed = "/steward.md";
            destinations = { };
          };
        in
        {
          inherit source;
          destination = toString source;
        }
      )
      [
        null
        "/home/example/system-wrapper"
      ];
  manifest = pkgs.writeText "generated-instruction-projections.json" (
    builtins.toJSON {
      inherit homeDirectory homeFiles;
      promptFiles =
        interactivePromptFiles
        ++ stewardPromptFiles
        ++ [
          {
            source = import ../../harnesses/hermes/interactive-instructions.nix { inherit pkgs; };
            destination = "${homeDirectory}/.hermes/config.yaml";
          }
        ];
    }
  );
in
{
  domain-generated-instruction-projections =
    pkgs.runCommand "domain-generated-instruction-projections"
      {
        nativeBuildInputs = [
          projection.python
          pkgs.nodejs
        ];
        PYTHONPATH = ../../quality/evaluations;
      }
      ''
        python ${./verify-generated-instructions.py} ${manifest} "$TMPDIR/instruction-filesystem"
        touch "$out"
      '';
}
