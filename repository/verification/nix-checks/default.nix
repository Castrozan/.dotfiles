{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ./helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };

  checkModuleArgs = {
    inherit (helpers) mkEvalCheck;
    inherit
      pkgs
      lib
      inputs
      self
      nixpkgs-version
      home-version
      helpers
      ;
  };

  checkModules = builtins.filter (
    checkModule:
    builtins.baseNameOf checkModule == "checks.nix"
    && builtins.baseNameOf (builtins.dirOf checkModule) == "__tests__"
  ) (lib.filesystem.listFilesRecursive self.outPath);
in
lib.foldl' lib.mergeAttrs { } (map (checkModule: import checkModule checkModuleArgs) checkModules)
