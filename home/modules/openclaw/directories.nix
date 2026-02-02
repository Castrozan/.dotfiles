{ lib, config, ... }:
let
  openclaw = config.openclaw;
  mainWorkspace = "${config.home.homeDirectory}/${openclaw.workspacePath}";
  directories = [
    "memory"
    "projects"
  ];
  mkDirs = base: lib.concatMapStringsSep "\n" (dir: "mkdir -p \"${base}/${dir}\"") directories;
in
{
  home.activation.openclawDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${mkDirs mainWorkspace}
  '';
}
