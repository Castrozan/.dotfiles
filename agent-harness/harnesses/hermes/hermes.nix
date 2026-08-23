{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  ...
}:
let
  version = "0.19.0";
  packageSpec = "hermes-agent[anthropic,cli]==${version}";

  configTemplate = import ./config.nix {
    inherit
      pkgs
      lib
      hostname
      isDarwin
      ;
  };
  soul = import ./soul.nix { inherit pkgs; };
  migration = import ./migration.nix { inherit pkgs; };

  runtimeDependencies = [
    pkgs.coreutils
    pkgs.git
    pkgs.ripgrep
    pkgs.nodejs
  ];

  hermes-agent = pkgs.writeShellApplication {
    name = "hermes";
    bashOptions = [ ];
    runtimeEnv = {
      HERMES_AGENT_VERSION = version;
      HERMES_AGENT_PACKAGE_SPEC = packageSpec;
      HERMES_AGENT_UV = "${pkgs.uv}/bin/uv";
      HERMES_AGENT_PYTHON = "${pkgs.python311}/bin/python3.11";
      HERMES_AGENT_CONFIG_TEMPLATE = "${configTemplate}";
      HERMES_AGENT_SOUL = "${soul}";
      HERMES_AGENT_HUMANIZE_SKILL = "${../../agent-instructions/skills/humanize/SKILL.md}";
      HERMES_AGENT_DOCS_SKILL = "${../../agent-instructions/skills/docs/SKILL.md}";
      HERMES_AGENT_USER_MEMORY = "${migration.userMemory}";
      HERMES_AGENT_AGENT_MEMORY = "${migration.agentMemory}";
      HERMES_AGENT_RETIRED_USER_MEMORY_ENTRY_PREFIXES = "${migration.retiredUserMemoryEntryPrefixes}";
      HERMES_AGENT_RETIRED_AGENT_MEMORY_ENTRY_PREFIXES = "${migration.retiredAgentMemoryEntryPrefixes}";
      HERMES_AGENT_MEMORY_SYNCHRONIZER = "${./scripts/synchronize-hermes-memory.py}";
      HERMES_AGENT_MEMORY_SYNCHRONIZER_PYTHON = "${pkgs.python312}/bin/python3.12";
      HERMES_AGENT_RUNTIME_PATH = lib.makeBinPath runtimeDependencies;
      HERMES_AGENT_BASH = "${pkgs.bash}/bin/bash";
      HERMES_AGENT_LAUNCH_SCRIPT = "${./scripts/hermes-launch}";
    };
    text = builtins.readFile ./scripts/hermes;
  };
in
{
  options.hermes.package = lib.mkOption {
    type = lib.types.package;
    default = hermes-agent;
    readOnly = true;
    description = "The Hermes Agent launcher package used across hermes modules";
  };

  config.home = {
    packages = [ hermes-agent ];
    file.".local/bin/hermes" = {
      source = "${hermes-agent}/bin/hermes";
      force = true;
    };
  };
}
