{ pkgs, ... }:
let
  # Local skills directory
  localSkillsDir = ../../../agents/skills;

  # Superpowers skills fetched directly (not a flake input)
  superpowersRepo = pkgs.fetchFromGitHub {
    owner = "obra";
    repo = "superpowers";
    rev = "b9e16498b9b6b06defa34cf0d6d345cd2c13ad31";
    hash = "sha256-0/biMK5A9DwXI/UeouBX2aopkUslzJPiNi+eZFkkzXI=";
  };
  superpowersSkillsDir = superpowersRepo + "/skills";

  # Get all directories with SKILL.md from a directory
  getSkillDirs =
    dir:
    if builtins.pathExists dir then
      builtins.filter (name: builtins.pathExists (dir + "/${name}/SKILL.md")) (
        builtins.attrNames (builtins.readDir dir)
      )
    else
      [ ];

  # Local skill directories
  localSkillDirs = getSkillDirs localSkillsDir;

  # Superpowers skill directories (prefixed to avoid conflicts)
  superpowersSkillDirs = getSkillDirs superpowersSkillsDir;

  # Create home.file entries for local skills
  localSkillSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = ".claude/skills/${dirname}";
      value = {
        source = localSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) localSkillDirs
  );

  # Create home.file entries for superpowers skills (prefixed with sp-)
  superpowersSkillSymlinks = builtins.listToAttrs (
    map (dirname: {
      name = ".claude/skills/sp-${dirname}";
      value = {
        source = superpowersSkillsDir + "/${dirname}";
        recursive = true;
      };
    }) superpowersSkillDirs
  );
in
{
  home.file = superpowersSkillSymlinks // localSkillSymlinks;
}
