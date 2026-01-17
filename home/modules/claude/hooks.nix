{ lib, ... }:
let
  hooksDir = ../../../agents/hooks;

  # Get all Python hook scripts from the hooks directory
  hookFiles = builtins.filter
    (name: lib.hasSuffix ".py" name)
    (builtins.attrNames (builtins.readDir hooksDir));

  # Create home.file entries for each hook script
  hookSymlinks = builtins.listToAttrs (map
    (filename: {
      name = ".claude/hooks/${filename}";
      value = {
        source = hooksDir + "/${filename}";
        executable = true;
      };
    })
    hookFiles);
in
{
  home.file = hookSymlinks;
}
