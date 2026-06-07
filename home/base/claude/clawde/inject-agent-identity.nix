{
  lib,
  self,
  peers ? [ ],
  personality,
}:
builtins.replaceStrings [ "@self@" "@peers@" ] [ self (lib.concatStringsSep ", " peers) ]
  personality
