{
  config,
  lib,
  pkgs,
  ...
}:
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  home.activation.installProductionCodexPlugin =
    lib.hm.dag.entryAfter
      [
        "linkGeneration"
        "seedCodexConfigAsMutableFile"
      ]
      ''
        ${pkgs.python312}/bin/python3 ${./scripts/register-managed-plugin.py} \
          ${config.codex.unwrappedPackage}/bin/codex \
          "${config.home.homeDirectory}/.local/share/agent-plugins/dotfiles" \
          "${config.home.homeDirectory}/.codex"
        ${pkgs.python312}/bin/python3 ${../../agent-instructions/production-plugin/scripts/retire-projections.py} \
          codex "${config.home.homeDirectory}" ${config.agentPlugins.bundle} \
          --codex ${config.codex.unwrappedPackage}/bin/codex
      '';
}
