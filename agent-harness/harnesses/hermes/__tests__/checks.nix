{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  pluginBundle = "/test/agent-plugin-bundle";
  hermesConfigTemplate = import ../config.nix {
    inherit pkgs pluginBundle;
  };
  hermesSoul = import ../soul.nix { inherit pkgs; };
  hermesMigration = import ../migration.nix { inherit pkgs; };
  hermesUserMemoryText = builtins.unsafeDiscardStringContext hermesMigration.userMemory.text;
  hermesAgentMemoryText = builtins.unsafeDiscardStringContext hermesMigration.agentMemory.text;
  hermesManagedMemoryText = "${hermesUserMemoryText}\n${hermesAgentMemoryText}";
  canonicalCore = builtins.readFile ../../../agent-instructions/core-rules/core.md;
  hermesIdentity = "You are Hermes Agent, an intelligent AI assistant created by Nous Research.";
  expectedHermesSoul = pkgs.writeText "expected-hermes-SOUL.md" "### Harness identity\n\n${hermesIdentity}\n\n${canonicalCore}";
  hermesHookCommandPath = "${pluginBundle}/plugin/native/hermes/hook-bridge";

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  retiredCoreMemoryFragments = [
    "Correction stance:"
    "Uncertainty:"
    "Interactive reply shape:"
    "Before returning control:"
    "Code style he enforces:"
    "Scripts:"
    "Git:"
  ];
in
{
  domain-hermes-bin-wrapper =
    mkEvalCheck "domain-hermes-bin-wrapper" (builtins.hasAttr ".local/bin/hermes" cfg.home.file)
      ".local/bin/hermes should be in home.file";

  domain-hermes-generated-configuration =
    pkgs.runCommand "domain-hermes-generated-configuration"
      {
        nativeBuildInputs = [
          (import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; }).python
        ];
        PYTHONPATH = ../../../quality/evaluations;
      }
      ''
        python ${./verify-generated-configuration.py} ${hermesConfigTemplate} ${lib.escapeShellArg hermesHookCommandPath}
        touch "$out"
      '';

  domain-hermes-soul-carries-canonical-core =
    pkgs.runCommand "domain-hermes-soul-carries-canonical-core" { }
      ''
        cmp ${hermesSoul} ${expectedHermesSoul}
        touch "$out"
      '';

  domain-hermes-memory-does-not-own-core =
    mkEvalCheck "domain-hermes-memory-does-not-own-core"
      (builtins.all (
        fragment: !(lib.hasInfix fragment hermesManagedMemoryText)
      ) retiredCoreMemoryFragments)
      "Hermes mutable memory may retain user facts and preferences but must not restate core, interactive, coding, scripting, or Git authority";
}
