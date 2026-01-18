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
      };
    })
    hookFiles);

  # Marker file to prevent home-manager from optimizing the hooks directory
  # into a single symlink to the nix store. Without this, all files in the
  # directory would be symlinks inside a read-only nix store directory,
  # causing "Read-only file system" errors on subsequent rebuilds.
  markerFile = {
    ".claude/hooks/.hm-keep" = {
      text = "";
    };
  };
in
{
  home.file = hookSymlinks // markerFile;
}
