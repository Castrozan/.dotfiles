{
  helpers,
  pkgs,
  self,
  ...
}:
let
  configuration = helpers.homeManagerTestConfigurationForEvaluatingSystem [
    self.homeManagerModules.claude-code
  ];
  plugin = configuration.home.file.".local/share/claude-context-mode".source;
  protocolPython = pkgs.python312.withPackages (packages: [ packages.mcp ]);
in
{
  context-mode-full-plugin-runtime = pkgs.runCommand "context-mode-full-plugin-runtime" { } ''
    ${protocolPython}/bin/python3 ${./verify-plugin.py} ${plugin}
    touch "$out"
  '';
}
