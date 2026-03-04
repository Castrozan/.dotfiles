{
  pkgs,
  config,
  lib,
  ...
}:
let
  passwordStoreDirectory = "${config.home.homeDirectory}/.password-store";

  nixSystemPaths = lib.concatStringsSep ":" [
    "${pkgs.pass-wayland}/bin"
    "${pkgs.gnupg}/bin"
    "${pkgs.git}/bin"
    "${pkgs.openssh}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${config.home.username}/bin"
    "${config.home.homeDirectory}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  passwordStoreGitSyncScript = pkgs.writeShellScript "password-store-git-sync" ''
    set -euo pipefail

    if [ ! -d "${passwordStoreDirectory}/.git" ]; then
      echo "Password store is not a git repo, skipping sync" >&2
      exit 0
    fi

    cd "${passwordStoreDirectory}"

    if ! ${pkgs.git}/bin/git diff --quiet 2>/dev/null || \
       ! ${pkgs.git}/bin/git diff --cached --quiet 2>/dev/null || \
       [ -n "$(${pkgs.git}/bin/git ls-files --others --exclude-standard 2>/dev/null)" ]; then
      ${pkgs.git}/bin/git add -A
      ${pkgs.git}/bin/git commit -m "auto-sync $(date -Iseconds)"
    fi

    ${pkgs.git}/bin/git pull --rebase 2>/dev/null || true
    ${pkgs.git}/bin/git push 2>/dev/null || true
  '';
in
{
  programs.password-store = {
    enable = true;
    package = pkgs.pass-wayland.withExtensions (exts: [ exts.pass-otp ]);
    settings = {
      PASSWORD_STORE_DIR = passwordStoreDirectory;
      PASSWORD_STORE_CLIP_TIME = "45";
      PASSWORD_STORE_GENERATED_LENGTH = "32";
    };
  };

  systemd.user.services.password-store-git-sync = {
    Unit = {
      Description = "Password store git sync (commit, pull, push)";
      After = [ "network-online.target" ];
    };

    Service = {
      Type = "oneshot";
      ExecStart = "${passwordStoreGitSyncScript}";
      Environment = [
        "PATH=${nixSystemPaths}"
        "HOME=${config.home.homeDirectory}"
        "GNUPGHOME=${config.home.homeDirectory}/.gnupg"
      ];
    };
  };

  systemd.user.timers.password-store-git-sync = {
    Unit = {
      Description = "Password store git sync timer";
    };

    Timer = {
      OnCalendar = "*:0/30";
      Persistent = true;
    };

    Install = {
      WantedBy = [ "timers.target" ];
    };
  };
}
