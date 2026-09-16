{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  annotatePackage = import ./herdr-annotate-package.nix { inherit pkgs lib; };
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
in
{
  home.packages = [ annotatePackage ];
  home.activation.linkHerdrAnnotate = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    run ${herdrPackage}/bin/herdr plugin link ${annotatePackage}/share/herdr/plugins/annotate --enabled
  '';
}
