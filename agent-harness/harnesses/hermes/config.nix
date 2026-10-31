{
  pkgs,
  pluginBundle,
}:
let
  hookCommand = "${pluginBundle}/plugin/native/hermes/hook-bridge";
in
pkgs.writeText "hermes-config.yaml" ''
  model:
    provider: openai-codex
    model: gpt-6.1-sol
  agent:
    reasoning_effort: xhigh
  auth:
    adopt_external_logins: false
  approvals:
    mode: "off"
  toolsets:
    - hermes-cli
  security:
    allow_lazy_installs: false
  plugins:
    enabled:
      - herdr-agent-state
      - dotfiles
  hooks_auto_accept: true
  hooks:
    pre_tool_call:
      - command: ${hookCommand}
        timeout: 10
    post_tool_call:
      - command: ${hookCommand}
        timeout: 20
''
