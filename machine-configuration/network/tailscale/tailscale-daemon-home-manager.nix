{ config, lib, ... }:
let
  tailscaleDaemonDirectoriesByInstaller = {
    nixSystemProfile = "/run/current-system/sw/bin";
    homeManagerUserPackages = "/etc/profiles/per-user/${config.home.username}/bin";
    standaloneNixProfile = "${config.home.homeDirectory}/.nix-profile/bin";
    homebrewAppleSilicon = "/opt/homebrew/bin";
    homebrewIntel = "/usr/local/bin";
    linuxDistributionPackageSbin = "/usr/sbin";
    linuxDistributionPackageBin = "/usr/bin";
  };

  tailscaleDaemonCandidates = lib.mapAttrsToList (
    _installer: directory: "${directory}/tailscaled"
  ) tailscaleDaemonDirectoriesByInstaller;
in
{
  home.activation.checkTailscaleDaemon = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      tailscaleDaemonPath=""
      for tailscaleDaemonCandidate in ${lib.escapeShellArgs tailscaleDaemonCandidates}; do
        if [ -x "$tailscaleDaemonCandidate" ]; then
          tailscaleDaemonPath="$tailscaleDaemonCandidate"
          break
        fi
      done
      if [ -z "$tailscaleDaemonPath" ] && command -v tailscaled >/dev/null 2>&1; then
        tailscaleDaemonPath="$(command -v tailscaled)"
      fi
      if [ -z "$tailscaleDaemonPath" ]; then
        echo "WARNING: tailscaled not found in any known install location."
        echo "  Declare it for this host in the dotfiles repo: services.tailscale.enable on NixOS and nix-darwin, or a homebrew.brews entry on darwin."
      fi
    '';
  };
}
