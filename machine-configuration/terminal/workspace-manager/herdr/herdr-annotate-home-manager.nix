{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  annotatePackage = import ./herdr-annotate-package.nix { inherit pkgs lib inputs; };
  herdrPackage = import ./herdr-package.nix { inherit pkgs inputs; };
in
{
  home.packages = [ annotatePackage ];
  home.activation.linkHerdrAnnotate = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    run ${herdrPackage}/bin/herdr plugin link ${annotatePackage}/share/herdr/plugins/annotate --enabled
  '';
}
