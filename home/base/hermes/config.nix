{ pkgs }:
pkgs.writeText "hermes-config.yaml" ''
  model: anthropic/claude-opus-4-8
  toolsets:
    - hermes-cli
  security:
    allow_lazy_installs: false
''
