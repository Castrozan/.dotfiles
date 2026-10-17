{ pkgs, ... }:
let
  btopWithMemoryTotals = import ../btop-package.nix { inherit pkgs; };
in
{
  domain-btop-memory-totals = pkgs.runCommand "btop-memory-totals" { } ''
    ${pkgs.python312}/bin/python3 ${./btop_memory_totals.py} ${btopWithMemoryTotals}/bin/btop
    touch "$out"
  '';
}
