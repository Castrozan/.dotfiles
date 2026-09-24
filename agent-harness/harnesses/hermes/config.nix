{
  pkgs,
  pluginBundle,
}:
let
  hookCommand = "${pluginBundle}/plugin/native/hermes/hook-bridge";
  projection = import ../../agent-instructions/instruction-projection.nix { inherit pkgs; };
  interactiveCommunication = import ./interactive-instructions.nix { inherit pkgs; };
  template = pkgs.writeText "hermes-config-template.yaml" ''
    model:
      provider: openai-codex
      model: gpt-5.5
    agent:
      reasoning_effort: xhigh
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
  '';
in
pkgs.runCommand "hermes-config.yaml" { nativeBuildInputs = [ projection.python ]; } ''
  python ${./scripts/render-hermes-configuration.py} ${template} ${interactiveCommunication} "$out"
''
