{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  rinPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../darwin
  ]
  ++ lib.optionals rinPrivateConfigExists [
    "${privateConfigRoot}/machines/rin/clawde-agents"
  ];
}
