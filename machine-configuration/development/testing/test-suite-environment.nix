{ pkgs }:
let
  pythonTestEnvironment = import ./python-test-environment.nix { inherit pkgs; };
in
pkgs.buildEnv {
  name = "dotfiles-test-suite-environment";
  paths = [
    pythonTestEnvironment
    (import ../../media/media-generation/video-ffmpeg-package.nix { inherit pkgs; })
    pkgs.neovim
    pkgs.nodejs_22
    pkgs.pyright
    pkgs.ripgrep
  ]
  ++ pkgs.lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.mpv;
}
