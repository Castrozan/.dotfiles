{
  config,
  pkgs,
  ...
}:
# Claude Code installs a plugin once and freezes it at that commit, so a marketplace
# this repository declares keeps shipping whatever build the machine first installed.
# Converging the install onto the marketplace checkout on every rebuild is what makes
# an upstream fix reach the machine instead of waiting for someone to notice it never
# arrived. Refreshing the marketplace itself stays with Claude Code: that clones over
# ssh, and activation runs without the user's agent, so it could only ever warn here.
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
