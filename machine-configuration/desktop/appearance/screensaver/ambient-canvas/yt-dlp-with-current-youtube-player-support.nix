{ pkgs }:
let
  version = "2026.11.23";
in
pkgs.yt-dlp.overridePythonAttrs (_: {
  inherit version;
  src = pkgs.fetchFromGitHub {
    owner = "yt-dlp";
    repo = "yt-dlp";
    tag = version;
    hash = "sha256-BpxnzY9GOs9sTv/ZWAwYiiJS7VfaMtp5HHOtXDAGgc0=";
  };
})
