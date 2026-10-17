{
  helpers,
  pkgs,
  self,
  ...
}:
let
  configuration = helpers.homeManagerTestConfigurationForEvaluatingSystem [
    self.homeManagerModules.claude-code
    ../default.nix
  ];
  configurationWithoutTrial = helpers.homeManagerTestConfigurationForEvaluatingSystem [
    self.homeManagerModules.claude-code
    { disabledModules = [ ../default.nix ]; }
  ];
  plugin = configuration.home.file.".local/share/claude-context-mode".source;
  protocolPython = pkgs.python312.withPackages (packages: [ packages.mcp ]);
in
{
  context-mode-removal-preserves-claude =
    helpers.mkEvalCheck "context-mode-removal-preserves-claude"
      (
        !(configurationWithoutTrial.home.file ? ".local/share/claude-context-mode")
        && builtins.all (
          package:
          !(builtins.elem (pkgs.lib.getName package) [
            "claude-context-mode"
            "context-mode"
          ])
        ) configurationWithoutTrial.home.packages
        &&
          configuration.home.file.".local/bin/claude".source
          == configurationWithoutTrial.home.file.".local/bin/claude".source
        &&
          configuration.home.file.".claude/settings.json.nix-source".source
          == configurationWithoutTrial.home.file.".claude/settings.json.nix-source".source
      )
      "Removing the trial must remove its commands and plugin while preserving normal Claude settings and launcher";

  context-mode-full-plugin-runtime = pkgs.runCommand "context-mode-full-plugin-runtime" { } ''
    ${protocolPython}/bin/python3 ${./verify-plugin.py} ${plugin}
    touch "$out"
  '';
}
