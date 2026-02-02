# SSH public keys for authorized_keys and known_hosts
# This file centralizes SSH key management for better maintainability
# Used by both NixOS (nixos.nix) and home-manager (home/ssh.nix) configurations
let
  sshHostsPath = ../../private-config/ssh-hosts.nix;
  sshHosts = if builtins.pathExists sshHostsPath then import sshHostsPath else { };

  # Phone SSH public key (for authorized_keys)
  phoneKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android";

  # Work PC SSH public key (for authorized_keys)
  workPcKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/";

  # Host key fingerprints (public, safe to expose)
  phoneHostKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOWURbP41AHeoQUC4qpSriTvVKWezdpPMGg1f3Ti7gyd";
  workPcHostKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPctlyhhY3Tf6RS/qs4aMUK/cIiZFG804XJFbd0ooWP/";

  # Known hosts entries — IPs from encrypted ssh-hosts.nix
  phoneKnownHost = if sshHosts ? phone then "[${sshHosts.phone}]:8022 ${phoneHostKey}" else null;
  workPcKnownHost = if sshHosts ? workpc then "${sshHosts.workpc} ${workPcHostKey}" else null;
in
{
  # List of all authorized SSH public keys
  authorizedKeys = [
    phoneKey
    workPcKey
  ];

  # Known hosts entries for SSH client
  knownHosts = builtins.filter (x: x != null) [
    phoneKnownHost
    workPcKnownHost
  ];
}
