{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  kiraPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../darwin

    ../../base/dev/git-toggle-user.nix

    ../../base/opencode
    ../../base/opencode/private.nix

    ../../base/browser/firefox.nix

    ../../base/editor/jetbrains-idea.nix
    ../../base/editor/scripts.nix
    ../../base/editor/zed-editor.nix

    ../../base/dev/aws.nix
    ../../base/dev/google-workspace-cli.nix
    ../../base/dev/mcporter.nix
    ../../base/dev/ralph-tui.nix
    ../../base/dev/tuisvn.nix
  ]
  ++ lib.optionals kiraPrivateConfigExists [
    "${privateConfigRoot}/machines/kira/clawde-pm.nix"
  ];
}
