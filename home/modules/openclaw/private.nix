{
  lib,
  config,
  ...
}:
let
  # Force rebuild trigger: update this timestamp when submodule changes aren't detected
  # Last updated: 2026-02-03T03:25
  inherit (config) openclaw;
  privateDir = ../../../private-config/openclaw;
  workspaceDir = privateDir + "/workspace";
  skillsDir = privateDir + "/skills";

  workspaceDirExists = builtins.pathExists workspaceDir;
  skillsDirExists = builtins.pathExists skillsDir;

  # Deploy workspace files (USER.md, IDENTITY.md, SOUL.md) with substitution
  privateWorkspaceFiles =
    if workspaceDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name) (
        builtins.attrNames (builtins.readDir workspaceDir)
      )
    else
      [ ];

  workspaceEntries = builtins.listToAttrs (
    map (filename: {
      name = filename;
      value = {
        text = openclaw.substituteAgentConfig (workspaceDir + "/${filename}");
        force = true;
      };
    }) privateWorkspaceFiles
  );

  # Deploy private skills (each directory with a SKILL.md)
  privateSkillDirs =
    if skillsDirExists then
      builtins.filter (name: builtins.pathExists (skillsDir + "/${name}/SKILL.md")) (
        builtins.attrNames (builtins.readDir skillsDir)
      )
    else
      [ ];

  skillEntries = builtins.listToAttrs (
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
          text = openclaw.substituteAgentConfig (skillDir + "/${file}");
          force = true;
        };
      }) regularFiles
    ) privateSkillDirs
  );
in
{
  home.file = lib.mkIf (workspaceDirExists || skillsDirExists) (
    openclaw.deployToWorkspace (workspaceEntries // skillEntries)
  );
}
