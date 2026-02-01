{ lib, config, ... }:
let
  workspacePath = config.openclaw.workspacePath;
  agentScriptsPath = ../../../agents/scripts;

  scriptFilenames = builtins.filter (name: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name) (
    builtins.attrNames (builtins.readDir agentScriptsPath)
  );

  scripts = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/scripts/${filename}";
      value.source = agentScriptsPath + "/${filename}";
    }) scriptFilenames
  );
in
{
  home.file = scripts;
}
