{
  pkgs,
  lib,
  ...
}:
let
  version = "0.16.0";
  packageSpec = "hermes-agent[anthropic,cli]==${version}";

  configTemplate = import ./config.nix { inherit pkgs; };
  migration = import ./migration.nix { inherit pkgs; };

  runtimeDependencies = [
    pkgs.coreutils
    pkgs.git
    pkgs.ripgrep
    pkgs.nodejs
  ];

  hermes-agent = pkgs.writeShellScriptBin "hermes" ''
    export HERMES_AGENT_VERSION="${version}"
    export HERMES_AGENT_PACKAGE_SPEC="${packageSpec}"
    export HERMES_AGENT_UV="${pkgs.uv}/bin/uv"
    export HERMES_AGENT_PYTHON="${pkgs.python311}/bin/python3.11"
    export HERMES_AGENT_CONFIG_TEMPLATE="${configTemplate}"
    export HERMES_AGENT_USER_MEMORY="${migration.userMemory}"
    export HERMES_AGENT_AGENT_MEMORY="${migration.agentMemory}"
    export HERMES_AGENT_RUNTIME_PATH="${lib.makeBinPath runtimeDependencies}"
    exec ${pkgs.bash}/bin/bash ${./scripts/hermes-launch} "$@"
  '';
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
