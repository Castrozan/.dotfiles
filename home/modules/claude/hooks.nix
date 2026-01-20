{lib, ...}: let
  hooksDir = ../../../agents/hooks;

  listHookScripts = dir:
    builtins.filter
    (name: lib.hasSuffix ".py" name || lib.hasSuffix ".sh" name)
    (builtins.attrNames (builtins.readDir dir));

  createSymlinksForHooks = files:
    builtins.listToAttrs (map
      (filename: {
        name = ".claude/hooks/${filename}";
        value = {
          source = hooksDir + "/${filename}";
          executable = lib.hasSuffix ".sh" filename;
        };
      })
      files);

  # Prevents home-manager from optimizing the hooks directory into a single
  # symlink to the nix store, which would cause read-only filesystem errors.
  preventDirectoryOptimization = {
    ".claude/hooks/.hm-keep".text = "";
  };
in {
  home.file = createSymlinksForHooks (listHookScripts hooksDir) // preventDirectoryOptimization;
}
