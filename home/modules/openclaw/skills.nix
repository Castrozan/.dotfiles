{ config, ... }:
let
  openclaw = config.openclaw;
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

  files = builtins.listToAttrs (
    builtins.concatMap (
      dirname:
      let
        skillDir = skillsSourcePath + "/${dirname}";
        entries = builtins.readDir skillDir;
        regularFiles = builtins.filter (name: entries.${name} == "regular") (builtins.attrNames entries);
      in
      map (file: {
        name = "skills/${dirname}/${file}";
        value.text = openclaw.substituteAgentConfig (skillDir + "/${file}");
      }) regularFiles
    ) skillDirectories
  );
in
{
  home.file = openclaw.deployToWorkspace files;
}
