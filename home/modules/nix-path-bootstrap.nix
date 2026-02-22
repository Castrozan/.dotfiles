{ config, ... }:
let
  nixMultiUserDaemonBinPath = "/nix/var/nix/profiles/default/bin";
  nixUserProfileBinPath = "${config.home.homeDirectory}/.nix-profile/bin";
  nixDaemonProfileScript = "/etc/profile.d/nix.sh";
  nixSingleUserProfileScript = "${config.home.homeDirectory}/.nix-profile/etc/profile.d/nix.sh";
in
{
  home.sessionPath = [
    nixMultiUserDaemonBinPath
    nixUserProfileBinPath
  ];

  home.file.".config/environment.d/10-nix-path.conf".text = ''
    PATH=${nixMultiUserDaemonBinPath}:${nixUserProfileBinPath}:$PATH
  '';

  programs.bash.enable = true;

  programs.bash.initExtra = ''
    if ! command -v nix &>/dev/null; then
      if [[ -f ${nixDaemonProfileScript} ]]; then
        source ${nixDaemonProfileScript}
      elif [[ -f ${nixSingleUserProfileScript} ]]; then
        source ${nixSingleUserProfileScript}
      fi
    fi
  '';
}
