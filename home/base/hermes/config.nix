{ pkgs }:
pkgs.writeText "hermes-config.yaml" ''
  model:
    provider: openai-codex
    model: gpt-5.5
  toolsets:
    - hermes-cli
  security:
    allow_lazy_installs: false
''
