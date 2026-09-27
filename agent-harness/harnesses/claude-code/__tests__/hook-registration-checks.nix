{
  pkgs,
  cfg,
  mkEvalCheck,
  ...
}:
{
  hooks-registration-verifies-the-active-settings-after-seeding =
    mkEvalCheck "hooks-registration-verifies-the-active-settings-after-seeding"
      (builtins.hasAttr "verifyDeployedProhibitedWordsAllowlist" cfg.home.activation)
      "The activation must verify host allowlists in generated and active Claude settings and managed Codex requirements";

  hooks-claude-generated-native-registrations =
    pkgs.runCommand "hooks-claude-generated-native-registrations" { }
      ''
        ${pkgs.python312}/bin/python3 ${../../../agent-instructions/rulesync/hooks/__tests__/verify_registrations.py} \
          ${cfg.home.file.".claude/settings.json.nix-source".source} claude
        touch "$out"
      '';
}
