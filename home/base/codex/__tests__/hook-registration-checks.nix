{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
}:
let
  parsedCodexHooksConfig = {
    hooks = import ../hooks/configuration.nix {
      inherit pkgs lib;
      hostname = "test";
    };
  };
  codexSystemManagedHooksConfig = import ../system-managed-hooks.nix {
    inherit pkgs lib;
    hostname = "test";
  };
  darwinConfigurationsSource = builtins.readFile ../../../../flake/darwin-configurations.nix;
  nixosConfigurationsSource = builtins.readFile ../../../../flake/nixos-configurations.nix;

  codexSessionStartGroups =
    if parsedCodexHooksConfig ? hooks && parsedCodexHooksConfig.hooks ? SessionStart then
      parsedCodexHooksConfig.hooks.SessionStart
    else
      [ ];
  firstCodexSessionStartGroup =
    if codexSessionStartGroups == [ ] then { } else builtins.head codexSessionStartGroups;

  codexHookEventCommands =
    eventName:
    let
      eventGroups =
        if parsedCodexHooksConfig ? hooks && parsedCodexHooksConfig.hooks ? ${eventName} then
          parsedCodexHooksConfig.hooks.${eventName}
        else
          [ ];
    in
    builtins.concatMap (group: map (hook: hook.command or "") (group.hooks or [ ])) eventGroups;

  codexHookEventRunsScript =
    eventName: scriptName:
    builtins.any (command: lib.hasInfix scriptName command) (codexHookEventCommands eventName);

  canonicalHooksEventDefinition = import ../../../../agents/hooks/event-to-dispatcher-map.nix;

  codexSupportedHookEvents = [
    "SessionStart"
    "PreToolUse"
    "PostToolUse"
    "Stop"
  ];

  codexHookEventNames = lib.attrNames (parsedCodexHooksConfig.hooks or { });

  codexEventsNotInTheSupportedCanonicalSubset = lib.filter (
    eventName: !(lib.elem eventName codexSupportedHookEvents)
  ) codexHookEventNames;

  supportedCanonicalEventsMissingFromTheCodexConfig = lib.filter (
    eventName: !(lib.elem eventName codexHookEventNames)
  ) codexSupportedHookEvents;

  supportedEventsNotDeclaredInTheCanonicalMap = lib.filter (
    eventName: !(lib.hasAttr eventName canonicalHooksEventDefinition.dispatchersByEvent)
  ) codexSupportedHookEvents;

  codexEventsWhoseCommandDivergesFromTheCanonicalDispatcher = lib.filter (
    eventName:
    !lib.hasAttr eventName canonicalHooksEventDefinition.dispatchersByEvent
    || !(lib.any (
      command: lib.hasInfix canonicalHooksEventDefinition.dispatchersByEvent.${eventName} command
    ) (codexHookEventCommands eventName))
  ) codexHookEventNames;

  codexRegistrationRefusesToDegradeWithoutPrivateConfig =
    let
      attempt = builtins.tryEval (
        builtins.toJSON (
          (import ../hooks/configuration.nix {
            inherit pkgs lib;
            hostname = "test";
            isDarwin = true;
            privateConfigRoot = "/nonexistent/private-config";
          }).PreToolUse
        )
      );
    in
    !attempt.success;
in
{
  codex-hooks-events-are-the-supported-canonical-subset =
    mkEvalCheck "codex-hooks-events-are-the-supported-canonical-subset"
      (
        codexEventsNotInTheSupportedCanonicalSubset == [ ]
        && supportedCanonicalEventsMissingFromTheCodexConfig == [ ]
        && supportedEventsNotDeclaredInTheCanonicalMap == [ ]
      )
      "Codex must register exactly the events in agents/hooks/event-to-dispatcher-map.nix that codex supports (${lib.concatStringsSep ", " codexSupportedHookEvents}) and nothing else; a hand-written Codex hook event is a second definition of the hook surface, and an event dropped from the supported list silently unregisters it. Codex events outside the supported canonical subset: ${lib.concatStringsSep ", " codexEventsNotInTheSupportedCanonicalSubset}. Supported canonical events missing from the Codex config: ${lib.concatStringsSep ", " supportedCanonicalEventsMissingFromTheCodexConfig}. Supported events not declared in the canonical map: ${lib.concatStringsSep ", " supportedEventsNotDeclaredInTheCanonicalMap}";

  codex-hooks-config-managed-file =
    mkEvalCheck "codex-hooks-config-managed-file"
      (
        !(builtins.hasAttr ".codex/hooks.json" cfg.home.file)
        && builtins.hasAttr "codex/requirements.toml" codexSystemManagedHooksConfig.environment.etc
        && lib.hasInfix "../home/base/codex/system-managed-hooks.nix" darwinConfigurationsSource
        && lib.hasInfix "../home/base/codex/system-managed-hooks.nix" nixosConfigurationsSource
      )
      "Codex hooks should be deployed through /etc/codex/requirements.toml on Darwin and NixOS so Codex treats them as managed and trusted";

  codex-hooks-config-current-schema = mkEvalCheck "codex-hooks-config-current-schema" (
    parsedCodexHooksConfig ? hooks && firstCodexSessionStartGroup ? hooks
  ) "Codex managed requirements should use the current top-level hooks schema";

  codex-hooks-config-session-start-every-source =
    mkEvalCheck "codex-hooks-config-session-start-every-source"
      ((firstCodexSessionStartGroup.matcher or "") == ".*")
      "Codex SessionStart must run on every source, not just compaction: herdr_agent_session_report_handler reports the pane's session id to herdr on startup and resume, and that report is what lets herdr resume the agent after a reboot. compaction_context_recovery_handler gates itself on source == compact, so widening the matcher does not fire the recovery directive outside compaction";

  codex-hooks-config-post-tool-use-dispatcher =
    mkEvalCheck "codex-hooks-config-post-tool-use-dispatcher"
      (codexHookEventRunsScript "PostToolUse" "post-tool-use-dispatcher.py")
      "Codex PostToolUse must run the same post-tool-use-dispatcher.py Claude registers; it composes auto-format, record-edited-source-file and nix-rebuild-trigger, and test_codex_surface_handler_composition guards that those three stay on the codex surface";

  codex-hooks-config-pre-tool-use-dispatcher =
    mkEvalCheck "codex-hooks-config-pre-tool-use-dispatcher"
      (codexHookEventRunsScript "PreToolUse" "pre-tool-use-dispatcher.py")
      "Codex PreToolUse must run the same pre-tool-use-dispatcher.py Claude registers (env-prefixed with the per-host PROHIBITED_WORDS_ALLOWED allowlist); it composes the prohibited-command/word guards, and test_codex_surface_handler_composition guards that they stay on the codex surface";

  codex-hooks-config-stop-dispatcher =
    mkEvalCheck "codex-hooks-config-stop-dispatcher"
      (codexHookEventRunsScript "Stop" "stop-dispatcher.py")
      "Codex Stop must run the same stop-dispatcher.py Claude registers; it composes lint-turn-review and herdr_agent_session_report on both surfaces and end-of-turn-format-guard on Claude only. The herdr report runs per turn as well as per session start so an agent that was already running when the hook shipped registers itself for reboot resume on its next turn instead of staying invisible until it restarts";

  codex-hooks-every-command-runs-its-canonical-dispatcher =
    mkEvalCheck "codex-hooks-every-command-runs-its-canonical-dispatcher"
      (codexEventsWhoseCommandDivergesFromTheCanonicalDispatcher == [ ])
      "every Codex hook event's command must run the dispatcher its event maps to in agents/hooks/event-to-dispatcher-map.nix, the single source of truth both harnesses import; a standalone command on a Codex event is a second definition of the hook surface and must be folded into that event's dispatcher as a handler carrying a tool_matcher. Events diverging from the canonical dispatcher: ${lib.concatStringsSep ", " codexEventsWhoseCommandDivergesFromTheCanonicalDispatcher}";

  codex-hooks-every-dispatcher-declares-its-surface =
    let
      dispatcherCommands = lib.filter (command: lib.hasInfix "-dispatcher.py" command) (
        lib.concatMap codexHookEventCommands (lib.attrNames (parsedCodexHooksConfig.hooks or { }))
      );
    in
    mkEvalCheck "codex-hooks-every-dispatcher-declares-its-surface"
      (
        dispatcherCommands != [ ]
        && lib.all (command: lib.hasInfix "--surface=codex" command) dispatcherCommands
      )
      "every Codex dispatcher registration must pass --surface=codex explicitly; the dispatchers default to the claude surface, so a registration that omits the flag silently runs Claude-only handlers (the reply-shape gate, the background-bash validator, the workspace injector) against a Codex session";

  codex-hooks-registration-fails-loud-when-private-config-is-missing =
    mkEvalCheck "codex-hooks-registration-fails-loud-when-private-config-is-missing"
      codexRegistrationRefusesToDegradeWithoutPrivateConfig
      "on a darwin host the codex hook registration must refuse to build when private-config/machines.nix is missing from the flake source; the previous silent fallback baked an empty PROHIBITED_WORDS_ALLOWED into the PreToolUse command and the guard re-blocked sessions on hosts whose per-machine allowlist file exists";
}
