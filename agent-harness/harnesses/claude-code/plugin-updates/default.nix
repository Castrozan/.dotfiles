{
  config,
  pkgs,
  ...
}:
# Claude Code installs a plugin once and freezes it at that commit, so a marketplace
# this repository declares keeps shipping whatever build the machine first installed.
# Following the declared marketplace ref on every rebuild is what makes an upstream
# fix reach the machine instead of waiting for someone to notice it never arrived.
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
