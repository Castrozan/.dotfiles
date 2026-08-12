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
  hermesHookCommandPath = builtins.unsafeDiscardStringContext "${hermesHooks.hermesHookCommand}";

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  hookCommandOccurrences =
    builtins.length (lib.splitString hermesHookCommandPath hermesConfigText) - 1;
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
}
