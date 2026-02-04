{
  lib,
  config,
  ...
}:
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
    agentName: basePath: prefix:
    let
      entries = builtins.readDir basePath;
      names = builtins.attrNames entries;
      regularFiles = builtins.filter (name: entries.${name} == "regular") names;
      subDirs = builtins.filter (name: entries.${name} == "directory") names;
    in
    (map (file: {
      name = "${prefix}/${file}";
      value.text = openclaw.substituteAgentConfig agentName (basePath + "/${file}");
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
        value.text = openclaw.substituteAgentConfig agentName (subPath + "/${file}");
      }) subFiles
    ) subDirs);

  # Generate skills files for a specific agent
  mkAgentFiles =
    agentName:
    builtins.listToAttrs (
      builtins.concatMap (
        dirname: collectFiles agentName (skillsSourcePath + "/${dirname}") "skills/${dirname}"
      ) skillDirectories
    );

  # Deploy to all enabled agents
  allFiles = lib.foldl' (
    acc: agentName: acc // (openclaw.deployToWorkspace agentName (mkAgentFiles agentName))
  ) { } (lib.attrNames openclaw.enabledAgents);
in
{
  home.file = allFiles;
}
