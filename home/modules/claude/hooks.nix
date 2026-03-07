{ lib, ... }:
let
  hooksDir = ../../../agents/hooks;

  listHookScripts =
    dir:
    builtins.filter (name: lib.hasSuffix ".py" name || lib.hasSuffix ".sh" name) (
      builtins.attrNames (builtins.readDir dir)
    );

  createSymlinksForHooks =
    files:
    builtins.listToAttrs (
      map (filename: {
        name = ".claude/hooks/${filename}";
        value = {
          source = hooksDir + "/${filename}";
          executable = lib.hasSuffix ".sh" filename;
        };
      }) files
    );

  preventDirectoryOptimization = {
    ".claude/hooks/.hm-keep".text = "";
  };
in
{
  home.file = createSymlinksForHooks (listHookScripts hooksDir) // preventDirectoryOptimization;
}
