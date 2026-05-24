{
  pkgs,
  lib,
  username,
  homeDir,
}:
lib.concatStringsSep ":" (
  [
    "${pkgs.tmux}/bin"
    "${pkgs.python312}/bin"
    "${pkgs.git}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isDarwin [
    "/opt/homebrew/bin"
    "/usr/local/bin"
  ]
  ++ [
    "/usr/bin"
    "/bin"
  ]
)
