{ config, ... }:
let
  workspacePath = config.openclaw.workspacePath;
  rulesPath = ../../../agents/rules;

  filenames = (builtins.attrNames (builtins.readDir rulesPath));

  rules = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/rules/${filename}";
      value.text = builtins.readFile (rulesPath + "/${filename}");
    }) filenames
  );
in
{
  home.file = rules;
}
