{ lib, config, ... }:
let
  workspace = "${config.home.homeDirectory}/${config.openclaw.workspacePath}";
  directories = [
    "memory"
    "projects"
  ];
in
{
  home.activation.openclawDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${lib.concatMapStringsSep "\n" (dir: "mkdir -p \"${workspace}/${dir}\"") directories}
  '';
}
