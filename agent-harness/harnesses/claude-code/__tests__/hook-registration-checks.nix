{ pkgs, cfg, ... }:
{
  hooks-claude-generated-native-registrations =
    pkgs.runCommand "hooks-claude-generated-native-registrations" { }
      ''
        ${pkgs.python312}/bin/python3 ${../../../agent-instructions/rulesync/hooks/__tests__/verify_registrations.py} \
          ${cfg.home.file.".claude/settings.json.nix-source".source} claude
        touch "$out"
      '';
}
