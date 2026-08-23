{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  hermesModuleArguments = {
    inherit pkgs lib;
    hostname = "test";
    isDarwin = false;
  };

  hermesHooks = import ../../../hooks/integrations/hermes/hermes-hooks.nix hermesModuleArguments;
  hermesConfigTemplate = import ../config.nix hermesModuleArguments;
  hermesConfigText = builtins.unsafeDiscardStringContext hermesConfigTemplate.text;
  hermesSoul = import ../soul.nix { inherit pkgs; };
  hermesSoulText = builtins.unsafeDiscardStringContext hermesSoul.text;
  hermesMigration = import ../migration.nix { inherit pkgs; };
  hermesUserMemoryText = builtins.unsafeDiscardStringContext hermesMigration.userMemory.text;
  hermesAgentMemoryText = builtins.unsafeDiscardStringContext hermesMigration.agentMemory.text;
  hermesManagedMemoryText = "${hermesUserMemoryText}\n${hermesAgentMemoryText}";
  canonicalCore = builtins.readFile ../../../agent-instructions/core-rules/core.md;
  hermesIdentity = "You are Hermes Agent, an intelligent AI assistant created by Nous Research.";
  hermesHookCommandPath = builtins.unsafeDiscardStringContext "${hermesHooks.hermesHookCommand}";

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  hookCommandOccurrences =
    builtins.length (lib.splitString hermesHookCommandPath hermesConfigText) - 1;
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

  domain-hermes-guards-every-tool-call =
    mkEvalCheck "domain-hermes-guards-every-tool-call" (hookCommandOccurrences == 2)
      "hermes must route both pre_tool_call and post_tool_call through the shared hook bridge; hermes is the only harness whose terminal tool runs shell commands, so dropping either entry leaves the prohibited-command guard off the one surface that needs it most";

  domain-hermes-accepts-its-own-hooks =
    mkEvalCheck "domain-hermes-accepts-its-own-hooks"
      (lib.hasInfix "hooks_auto_accept: true" hermesConfigText)
      "without hooks_auto_accept the shell-hook allowlist prompt gates registration, and every non-TTY launch silently skips the guards with nothing but a log line; the store path also changes on each rebuild, so a one-off manual approval would expire the next time the hooks change";

  domain-hermes-soul-carries-canonical-core =
    mkEvalCheck "domain-hermes-soul-carries-canonical-core"
      (hermesSoulText == "${hermesIdentity}\n\n${canonicalCore}")
      "Hermes SOUL.md must preserve its harness identity and carry the exact canonical core as stable session-long authority";

  domain-hermes-interactive-sessions-carry-humanize =
    mkEvalCheck "domain-hermes-interactive-sessions-carry-humanize"
      (lib.hasInfix "<interactive-session>" hermesConfigText)
      "Hermes CLI and gateway sessions must receive the same interactive Humanize contract as the other interactive harnesses";

  domain-hermes-memory-does-not-own-core =
    mkEvalCheck "domain-hermes-memory-does-not-own-core"
      (builtins.all (
        fragment: !(lib.hasInfix fragment hermesManagedMemoryText)
      ) retiredCoreMemoryFragments)
      "Hermes mutable memory may retain user facts and preferences but must not restate core, interactive, coding, scripting, or Git authority";
}
