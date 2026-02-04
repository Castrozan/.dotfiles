{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  # Use absolute paths to bypass flake's git tree tracking
  # Requires --impure flag for rebuild
  privateDir = /. + homeDir + "/.dotfiles/private-config/openclaw";
  workspaceDir = privateDir + "/workspace";
  skillsDir = privateDir + "/skills";

  workspaceDirExists = builtins.pathExists workspaceDir;
  skillsDirExists = builtins.pathExists skillsDir;

  # Get list of private workspace files (USER.md, IDENTITY.md, SOUL.md)
  privateWorkspaceFiles =
    if workspaceDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name) (
        builtins.attrNames (builtins.readDir workspaceDir)
      )
    else
      [ ];

  # Get list of private skill directories
  privateSkillDirs =
    if skillsDirExists then
      builtins.filter (name: builtins.pathExists (skillsDir + "/${name}/SKILL.md")) (
        builtins.attrNames (builtins.readDir skillsDir)
      )
    else
      [ ];

  # Generate workspace entries for a specific agent
  mkAgentWorkspaceEntries =
    agentName:
    builtins.listToAttrs (
      map (filename: {
        name = filename;
        value = {
          text = openclaw.substituteAgentConfig agentName (workspaceDir + "/${filename}");
          force = true;
        };
      }) privateWorkspaceFiles
    );

  # Generate skill entries for a specific agent
  mkAgentSkillEntries =
    agentName:
    builtins.listToAttrs (
      builtins.concatMap (
        dirname:
        let
          skillDir = skillsDir + "/${dirname}";
          entries = builtins.readDir skillDir;
          regularFiles = builtins.filter (name: entries.${name} == "regular") (builtins.attrNames entries);
        in
        map (file: {
          name = "skills/${dirname}/${file}";
          value = {
            text = openclaw.substituteAgentConfig agentName (skillDir + "/${file}");
            force = true;
          };
        }) regularFiles
      ) privateSkillDirs
    );

  # Deploy to all enabled agents
  allFiles = lib.foldl' (
    acc: agentName:
    let
      entries = mkAgentWorkspaceEntries agentName // mkAgentSkillEntries agentName;
    in
    acc // (openclaw.deployToWorkspace agentName entries)
  ) { } (lib.attrNames openclaw.enabledAgents);
in
{
  home.file = lib.mkIf (workspaceDirExists || skillsDirExists) allFiles;
}
