{ pkgs, lib }:
let
  projection = import ../instruction-projection.nix { inherit pkgs; };
  homeDirectory = "/home/instruction-fixture";
  moduleArguments = {
    inherit pkgs lib;
    hostname = "test";
    config.home.homeDirectory = homeDirectory;
    config.agentPlugins.bundle = productionBundle;
  };
  moduleHomeFiles = map (module: (import module moduleArguments).home.file) [
    ../dotfiles-checkout-agent-surfaces/dotfiles-repo-skills-home-manager.nix
    ../dotfiles-checkout-agent-surfaces/dotfiles-repo-agent-instructions-home-manager.nix
    ../../harnesses/opencode/agents/subagents.nix
    ../../harnesses/codex/global-instructions.nix
    ../../harnesses/opencode/instructions/global-instructions.nix
    ../../harnesses/pi/global-instructions.nix
  ];
  productionSource = import ../production-plugin {
    inherit pkgs lib homeDirectory;
    hostname = "test";
    chromePackage = pkgs.google-chrome;
  };
  productionBundle = (import ../../plugin-distribution { inherit pkgs; }).buildPlugin {
    source = productionSource;
  };
  homeFileDefinitions = builtins.foldl' (all: files: all // files) {
    ".hermes/SOUL.md".source = import ../../harnesses/hermes/soul.nix { inherit pkgs; };
    ".hermes/plugins/dotfiles".source = "${productionBundle}/plugin";
    ".local/share/agent-plugins/dotfiles/plugin".source = "${productionBundle}/plugin";
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
      bundle = productionBundle;
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
