{ hostname, pkgs, ... }:
let
  interactiveAgentSkills =
    import
      ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      {
        inherit hostname;
      };

  skillInstallModuleDirectory =
    skillName: interactiveAgentSkills.skillSourceDirectoryByName.${skillName} + "/install";

  skillNamesWithInstallModule = builtins.filter (
    skillName: builtins.pathExists (skillInstallModuleDirectory skillName + "/default.nix")
  ) interactiveAgentSkills.allSkillNames;

  installModuleAcceptsOnlyPkgs =
    skillName:
    let
      installModule = import (skillInstallModuleDirectory skillName);
      installModuleArgs = builtins.functionArgs installModule;
    in
    builtins.length (builtins.attrNames installModuleArgs) == 1 && installModuleArgs ? pkgs;

  skillNamesAutoWiredHere = builtins.filter installModuleAcceptsOnlyPkgs skillNamesWithInstallModule;

  packagesFromSkillInstallModules = builtins.concatLists (
    map (
      skillName:
      let
        installModule = import (skillInstallModuleDirectory skillName) {
          inherit pkgs;
        };
      in
      installModule.packages or [ ]
    ) skillNamesAutoWiredHere
  );
in
{
  home.packages = packagesFromSkillInstallModules;
}
