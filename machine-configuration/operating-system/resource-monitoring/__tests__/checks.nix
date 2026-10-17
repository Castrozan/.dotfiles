{ pkgs, ... }:
let
  btopWithMemoryTotals = import ../btop-package.nix { inherit pkgs; };
  patchedBtopSource = pkgs.applyPatches {
    name = "btop-system-process-group-source";
    inherit (btopWithMemoryTotals) src patches;
  };
in
{
  domain-btop-memory-totals = pkgs.runCommand "btop-memory-totals" { } ''
    ${pkgs.python312}/bin/python3 ${./btop}/memory_totals.py ${btopWithMemoryTotals}/bin/btop
    touch "$out"
  '';
  domain-btop-system-process-group =
    pkgs.runCommand "btop-system-process-group" { nativeBuildInputs = [ pkgs.stdenv.cc ]; }
      ''
        $CXX -std=c++20 -I ${patchedBtopSource}/src -I ${../.} ${./btop}/system_process_group.cpp -o contract
        ./contract
        touch "$out"
      '';
}
