{
  pkgs,
  lib,
  ...
}:
let
  claudePluginSkillPorter = pkgs.runCommand "opencode-claude-plugin-skill-porter" { } ''
    mkdir -p "$out"
    cp ${./claude-plugin-port}/*.py "$out"/
    cp ${../claude-code/plugins/installed_plugin_discovery.py} "$out/installed_plugin_discovery.py"
  '';
in
{
  home.activation.opencodeClaudePluginSkillPort = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${pkgs.python312}/bin/python3 ${claudePluginSkillPorter}/port_claude_plugin_skills_to_opencode.py || true
  '';
}
