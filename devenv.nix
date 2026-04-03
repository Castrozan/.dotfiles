{ pkgs, ... }:

{
  packages = [
    pkgs.python312
    pkgs.postgresql_16
  ];
}
