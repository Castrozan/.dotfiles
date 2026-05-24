{
  pkgs,
  lib,
  isDarwin,
  ...
}:
{
  home.sessionPath = lib.optionals isDarwin [
    "/run/current-system/sw/bin"
    "/nix/var/nix/profiles/default/bin"
    "/usr/bin"
    "/bin"
  ];

  home.sessionVariables = {
    OBSIDIAN_HOME = "$HOME/vault";
    EDITOR = "code";
    TZDIR = "${pkgs.tzdata}/share/zoneinfo";
  };
}
