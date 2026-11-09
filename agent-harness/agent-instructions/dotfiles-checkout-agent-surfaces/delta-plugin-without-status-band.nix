{ pkgs }:
pkgs.applyPatches {
  name = "delta-claude-plugin-without-status-band";
  src = pkgs.fetchFromGitHub {
    owner = "zed-industries";
    repo = "delta-claude";
    rev = "9c6cac8a11e26c9932f0cc491fd6393c175f0b25";
    hash = "sha256-N5Mr52ew6KOr36YeLVsc9T4gcjR7DZuOv0dN1p1/LpQ=";
  };
  patches = [ ./patches/delta-plugin-without-status-band.patch ];
}
