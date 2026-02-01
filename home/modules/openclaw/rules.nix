{ config, ... }:
let
  cfg = config.openclaw;
  workspacePath = cfg.workspacePath;
  rulesPath = ../../../agents/rules;
  subs = cfg.substitutions;

  filenames = (builtins.attrNames (builtins.readDir rulesPath));

  rules = builtins.listToAttrs (
    map (filename: {
      name = "${workspacePath}/rules/${filename}";
      value.text = builtins.replaceStrings (builtins.elemAt subs 0) (builtins.elemAt subs 1) (
        builtins.readFile (rulesPath + "/${filename}")
      );
    }) filenames
  );
in
{
  home.file = rules;
}
