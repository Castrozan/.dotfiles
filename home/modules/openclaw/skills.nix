{ config, ... }:
let
  inherit (config) openclaw;
  skillsSourcePath = ../../../agents/skills;

  # Private skills live in private-config/openclaw/skills/
  excludedSkills = [
    "bot-bridge"
    "whatsapp-polling"
    "openclaw-medicine"
  ];
  skillDirectories = builtins.filter (
    name:
    (builtins.readDir skillsSourcePath).${name} == "directory" && !builtins.elem name excludedSkills
  ) (builtins.attrNames (builtins.readDir skillsSourcePath));

  # Collect files from a directory, recursing one level into subdirectories
  collectFiles =
    basePath: prefix:
    let
      entries = builtins.readDir basePath;
      names = builtins.attrNames entries;
      regularFiles = builtins.filter (name: entries.${name} == "regular") names;
      subDirs = builtins.filter (name: entries.${name} == "directory") names;
    in
    (map (file: {
      name = "${prefix}/${file}";
      value.text = openclaw.substituteAgentConfig (basePath + "/${file}");
    }) regularFiles)
    ++ (builtins.concatMap (
      subdir:
      let
        subPath = basePath + "/${subdir}";
        subEntries = builtins.readDir subPath;
        subFiles = builtins.filter (name: subEntries.${name} == "regular") (builtins.attrNames subEntries);
      in
      map (file: {
        name = "${prefix}/${subdir}/${file}";
        value.text = openclaw.substituteAgentConfig (subPath + "/${file}");
      }) subFiles
    ) subDirs);

  files = builtins.listToAttrs (
    builtins.concatMap (
      dirname: collectFiles (skillsSourcePath + "/${dirname}") "skills/${dirname}"
    ) skillDirectories
  );
in
{
  home.file = openclaw.deployToWorkspace files;
}
