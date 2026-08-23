{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
}:
let
  hermesHooks = import ../../hooks/integrations/hermes/hermes-hooks.nix {
    inherit
      pkgs
      lib
      hostname
      isDarwin
      ;
  };
  interactiveCommunication = builtins.readFile ../../agent-instructions/skills/humanize/interactive-communication.md;
  indentedInteractiveCommunication =
    lib.replaceStrings [ "\n" ] [ "\n      " ]
      interactiveCommunication;
in
pkgs.writeText "hermes-config.yaml" ''
  model:
    provider: openai-codex
    model: gpt-5.5
  agent:
    reasoning_effort: xhigh
    system_prompt: |
      ${indentedInteractiveCommunication}
  toolsets:
    - hermes-cli
  security:
    allow_lazy_installs: false
  hooks_auto_accept: true
  hooks:
    pre_tool_call:
      - command: ${hermesHooks.hermesHookCommand}
        timeout: 10
    post_tool_call:
      - command: ${hermesHooks.hermesHookCommand}
        timeout: 20
''
