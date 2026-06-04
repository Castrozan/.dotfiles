{ pkgs, ... }:
let
  skillSetBuilders = import ./skill-set-builders.nix;

  skillNamesWithInstallModule = builtins.filter (
    skillName:
    builtins.pathExists (skillSetBuilders.dotfilesSkillsDirectory + "/${skillName}/install/default.nix")
  ) skillSetBuilders.allSkillNames;

  installModuleAcceptsOnlyPkgs =
    skillName:
    let
      installModule = import (skillSetBuilders.dotfilesSkillsDirectory + "/${skillName}/install");
      installModuleArgs = builtins.functionArgs installModule;
    in
    builtins.length (builtins.attrNames installModuleArgs) == 1 && installModuleArgs ? pkgs;

  skillNamesAutoWiredHere = builtins.filter installModuleAcceptsOnlyPkgs skillNamesWithInstallModule;

  packagesFromSkillInstallModules = builtins.concatLists (
    map (
      skillName:
      let
        installModule = import (skillSetBuilders.dotfilesSkillsDirectory + "/${skillName}/install") {
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
