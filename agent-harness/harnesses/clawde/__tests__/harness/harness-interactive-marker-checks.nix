{
  pkgs,
  mkEvalCheck,
  cfgWithBothHarnesses,
  cfgWithWorkspaceProfileAgent,
  claudeCommandsOf,
}:
let
  interactiveSessionSystemPromptFile = builtins.unsafeDiscardStringContext (
    toString cfgWithWorkspaceProfileAgent.claude.interactiveSessionSystemPromptFile
  );

  exportsTheInteractiveMarker =
    harnessCommandWithContext:
    let
      harnessCommand = builtins.unsafeDiscardStringContext harnessCommandWithContext;
    in
    pkgs.lib.hasInfix "AGENT_INTERACTIVE_PREFERENCES_PATH=${interactiveSessionSystemPromptFile} command claude" harnessCommand
    && pkgs.lib.hasInfix "--append-system-prompt-file ${interactiveSessionSystemPromptFile} " harnessCommand;

  launchCommandOnEveryHarnessOf =
    agentName:
    (builtins.fromJSON (
      builtins.unsafeDiscardStringContext
        cfgWithBothHarnesses.home.file."clawde/launch-config/${agentName}.json".text
    )).harness_launch_commands;

  exportsAnEmptyInteractiveMarker =
    harnessCommandWithContext:
    let
      harnessCommand = builtins.unsafeDiscardStringContext harnessCommandWithContext;
    in
    pkgs.lib.hasInfix "AGENT_INTERACTIVE_PREFERENCES_PATH= command claude" harnessCommand
    && !(pkgs.lib.hasInfix "--append-system-prompt-file" harnessCommand);
in
{
  clawde-interactive-session-agent-launches-with-the-interactive-prompt-and-marker =
    mkEvalCheck "clawde-interactive-session-agent-launches-with-the-interactive-prompt-and-marker"
      (
        let
          commands = claudeCommandsOf "agent-with-interactive-settings-and-workspace-profile";
        in
        exportsTheInteractiveMarker (builtins.elemAt commands 0)
        && builtins.all exportsAnEmptyInteractiveMarker (builtins.tail commands)
        && builtins.all exportsAnEmptyInteractiveMarker (claudeCommandsOf "agent-without-workspace-profile")
      )
      "a human-driven agent's persistent launch must append the interactive system prompt and export its marker so the interactive reply hooks judge its turns, while its run-once and channel turns and every other agent export an empty marker that an inherited one cannot leak through";

  clawde-no-launch-command-inherits-the-interactive-session-marker =
    mkEvalCheck "clawde-no-launch-command-inherits-the-interactive-session-marker"
      (pkgs.lib.all pkgs.lib.id (
        pkgs.lib.mapAttrsToList (
          harnessName: launchCommand:
          pkgs.lib.hasInfix "AGENT_INTERACTIVE_PREFERENCES_PATH= ${cfgWithBothHarnesses.clawde.harnesses.${harnessName}.binaryInvocation} " launchCommand
        ) (launchCommandOnEveryHarnessOf "agent-on-codex")
      ))
      "interactive detection trusts the marker alone, so an agent that never opted into claudeInteractiveSessionSettings must clear it on every harness: inherited from a keyboard session that started the fleet, it would put the interactive reply hooks on an unattended agent that never received the rules they judge";
}
