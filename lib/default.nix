{ lib, ... }:
{
  # use path relative to the root of the project
  relativeToRoot = lib.path.append ../.;

  # Helper function to scan for .nix files in a directory
  scanPaths =
    path:
    builtins.map (f: (path + "/${f}")) (
      builtins.attrNames (
        lib.attrsets.filterAttrs (
          path: _type:
          (_type == "directory") # include directories
          || (
            (path != "default.nix") # ignore default.nix
            && (lib.strings.hasSuffix ".nix" path) # include .nix files
          )
        ) (builtins.readDir path)
      )
    );

  # Helper function to generate a set of attributes for each system
  forAllSystems = func: lib.genAttrs [ "x86_64-linux" ] func;

  # Helper function to check if a configuration can be evaluated
  canEvaluate =
    config:
    builtins.tryEval config != {
      success = false;
      value = false;
    };

  # Helper function to test home directory paths
  testHomeDirectory =
    homeManagerConfig:
    let
      homeDir = homeManagerConfig.home.homeDirectory or null;
    in
    {
      success = homeDir != null;
      message = if homeDir != null then "Home directory: ${homeDir}" else "Home directory not set";
    };

  # Helper function to test system configuration
  testSystemConfig =
    nixosConfig:
    let
      systemBuild = nixosConfig.config.system.build.toplevel or null;
    in
    {
      success = systemBuild != null;
      message = if systemBuild != null then "System build available" else "System build not available";
    };
}
