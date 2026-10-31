{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:
let
  hermesRuntime = inputs.hermes.packages.${pkgs.stdenv.hostPlatform.system}.minimal.override {
    extraDependencyGroups = [ "anthropic" ];
  };

  configTemplate = import ./config.nix {
    inherit pkgs;
    pluginBundle = config.agentPlugins.bundle;
  };
  soul = import ./soul.nix { inherit pkgs; };

  runtimeDependencies = [
    pkgs.coreutils
    pkgs.git
    pkgs.ripgrep
    pkgs.nodejs_22
  ];

  hermes-agent = pkgs.writeShellApplication {
    name = "hermes";
    bashOptions = [ ];
    runtimeEnv = {
      HERMES_AGENT_BINARY = "${hermesRuntime}/bin/hermes";
      HERMES_AGENT_CONFIG_TEMPLATE = "${configTemplate}";
      HERMES_AGENT_SOUL = "${soul}";
      HERMES_AGENT_RUNTIME_PATH = lib.makeBinPath runtimeDependencies;
      HERMES_AGENT_BASH = "${pkgs.bash}/bin/bash";
      HERMES_AGENT_LAUNCH_SCRIPT = "${./scripts/hermes-launch}";
    };
    text = builtins.readFile ./scripts/hermes;
  };
in
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  options.hermes.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = hermesRuntime;
    readOnly = true;
    description = "Pinned upstream Hermes runtime with its bundled assets and native plugin loader.";
  };

  options.hermes.package = lib.mkOption {
    type = lib.types.package;
    default = hermes-agent;
    readOnly = true;
    description = "The Hermes Agent launcher package used across hermes modules";
  };

  config.home = {
    activation.retireHermesPartialSkills = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
      ${pkgs.python312}/bin/python3 ${../../agent-instructions/production-plugin/scripts/retire-projections.py} \
        hermes "${config.home.homeDirectory}" ${config.agentPlugins.bundle}
    '';
    packages = [ hermes-agent ];
    file = {
      ".local/bin/hermes" = {
        source = "${hermes-agent}/bin/hermes";
        force = true;
      };
      ".hermes/plugins/dotfiles".source = "${config.agentPlugins.bundle}/plugin";
      ".hermes/.no-bundled-skills".text = "";
    };
  };
}
