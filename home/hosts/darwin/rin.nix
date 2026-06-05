{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  rinPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../darwin

    ../../base/claude/agents/silver.nix
  ]
  ++ lib.optionals rinPrivateConfigExists [
    "${privateConfigRoot}/machines/rin/clawde-pm.nix"
  ];
}
