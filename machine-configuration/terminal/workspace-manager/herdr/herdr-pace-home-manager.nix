{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  pacePackage = inputs.herdr-pace.packages.${pkgs.stdenv.hostPlatform.system}.default;
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
in
{
  home.packages = [ pacePackage ];
  home.activation.linkHerdrPace = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    run ${herdrPackage}/bin/herdr plugin unlink castrozan.speed-read
    run ${herdrPackage}/bin/herdr plugin link ${pacePackage}/share/herdr-plugin --enabled
  '';
}
