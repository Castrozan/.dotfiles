{
  pkgs,
  lib,
  config,
  ...
}:
let
  pythonEnvironment = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.pyyaml ]);

  skillUsageSource = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./skill_usage.py
      ./skill_load_events.py
      ./skill_catalogue.py
    ];
  };

  skillUsage = pkgs.writeShellScriptBin "skill-usage" ''
    exec ${pythonEnvironment}/bin/python ${skillUsageSource}/skill_usage.py \
      --plugin-root ${config.agentPlugins.bundle}/plugin \
      --repository ${lib.escapeShellArg "${config.home.homeDirectory}/.dotfiles"} \
      "$@"
  '';
in
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  home.packages = [ skillUsage ];
}
