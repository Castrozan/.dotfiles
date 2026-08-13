{
  config,
  pkgs,
  ...
}:
{
  home.activation.updateEnabledClaudePlugins = {
    after = [ "seedClaudeSettingsAsMutableFile" ];
    before = [ ];
    data = ''
      PATH="${config.claude.unwrappedPackage}/bin:$PATH" \
        ${pkgs.python312}/bin/python3 ${./update_enabled_plugins.py}
    '';
  };
}
