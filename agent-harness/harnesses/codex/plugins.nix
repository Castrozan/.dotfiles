{
  config,
  lib,
  pkgs,
  ...
}:
let
  codexExecutable = "${config.codex.unwrappedPackage}/bin/codex";
  registration = pkgs.replaceVars ./scripts/register-managed-plugin.py {
    codex = codexExecutable;
  };
  retirement =
    pkgs.replaceVars ../../agent-instructions/production-plugin/scripts/retire-projections.py
      {
        codex = codexExecutable;
      };
in
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  home.activation.installProductionCodexPlugin =
    lib.hm.dag.entryAfter
      [
        "linkGeneration"
        "seedCodexConfigAsMutableFile"
      ]
      ''
        ${pkgs.python312}/bin/python3 ${registration} \
          "${config.home.homeDirectory}/.local/share/agent-plugins/dotfiles" \
          "${config.home.homeDirectory}/.codex"
        ${pkgs.python312}/bin/python3 ${retirement} \
          codex "${config.home.homeDirectory}" ${config.agentPlugins.bundle}
      '';
}
