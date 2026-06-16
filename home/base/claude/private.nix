{ lib, hostname, ... }:
let
  privateConfigDir = ../../../private-config/claude;
  agentsDir = privateConfigDir + "/agents";
  commandsDir = privateConfigDir + "/commands";
  sharedSkillsDir = privateConfigDir + "/skills";
  perMachineSkillsDir = ../../../private-config/machines + "/${hostname}/skills";

  agentsDirExists = builtins.pathExists agentsDir;
  commandsDirExists = builtins.pathExists commandsDir;
  sharedSkillsDirExists = builtins.pathExists sharedSkillsDir;
  perMachineSkillsDirExists = builtins.pathExists perMachineSkillsDir;

  privateAgentFiles =
    if agentsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
        builtins.attrNames (builtins.readDir agentsDir)
      )
    else
      [ ];

  privateCommandFiles =
    if commandsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
        builtins.attrNames (builtins.readDir commandsDir)
      )
    else
      [ ];

  skillDirNamesIn =
    skillsDir:
    builtins.filter (
      name: name != ".gitkeep" && builtins.pathExists (skillsDir + "/${name}/SKILL.md")
    ) (builtins.attrNames (builtins.readDir skillsDir));

  privateAgentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/agents/${filename}";
      value = {
        source = "${agentsDir}/${filename}";
      };
    }) privateAgentFiles
  );

  privateCommandSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/commands/${filename}";
      value = {
        source = "${commandsDir}/${filename}";
      };
    }) privateCommandFiles
  );

  skillSymlinksFrom =
    skillsDir:
    builtins.listToAttrs (
      map (dirname: {
        name = ".claude/skills/${dirname}";
        value = {
          source = "${skillsDir}/${dirname}";
          recursive = true;
        };
      }) (skillDirNamesIn skillsDir)
    );

  sharedSkillSymlinks = if sharedSkillsDirExists then skillSymlinksFrom sharedSkillsDir else { };
  perMachineSkillSymlinks =
    if perMachineSkillsDirExists then skillSymlinksFrom perMachineSkillsDir else { };
in
{
  home.file =
    lib.mkIf
      (agentsDirExists || commandsDirExists || sharedSkillsDirExists || perMachineSkillsDirExists)
      (privateAgentSymlinks // privateCommandSymlinks // sharedSkillSymlinks // perMachineSkillSymlinks);
}
