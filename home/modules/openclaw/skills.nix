{ config, ... }:
let
  workspacePath = config.openclaw.workspacePath;
  skillsPath = ../../../agents/skills;

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
        value.text = builtins.readFile (skillDir + "/${file}");
      }) files
    ) filenames
  );
in
{
  home.file = skills;
}
