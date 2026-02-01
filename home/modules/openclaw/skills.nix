{ config, ... }:
let
  cfg = config.openclaw;
  workspacePath = cfg.workspacePath;
  skillsPath = ../../../agents/skills;
  subs = cfg.substitutions;

  filenames = builtins.filter (name: (builtins.readDir skillsPath).${name} == "directory") (
    builtins.attrNames (builtins.readDir skillsPath)
  );

  skills = builtins.listToAttrs (
    builtins.concatMap (
      dirname:
      let
        skillDir = skillsPath + "/${dirname}";
        entries = builtins.readDir skillDir;
        files = builtins.filter (name: entries.${name} == "regular") (builtins.attrNames entries);
      in
      map (file: {
        name = "${workspacePath}/skills/${dirname}/${file}";
        value.text = builtins.replaceStrings (builtins.elemAt subs 0) (builtins.elemAt subs 1) (
          builtins.readFile (skillDir + "/${file}")
        );
      }) files
    ) filenames
  );
in
{
  home.file = skills;
}
