# SSH public keys for authorized_keys and known_hosts
# This file centralizes SSH key management for better maintainability
# Used by both NixOS (nixos.nix) and home-manager (home/ssh.nix) configurations
let
  # Phone SSH public key (for authorized_keys)
  phoneKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android";

  # Work PC SSH public key (for authorized_keys)
  workPcKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/";

  # Phone known_hosts entry (for SSH client)
  phoneKnownHost = "[192.168.7.8]:8022 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOWURbP41AHeoQUC4qpSriTvVKWezdpPMGg1f3Ti7gyd";
in
{
  # List of all authorized SSH public keys
  authorizedKeys = [
    phoneKey
    workPcKey
  ];
  
  # Known hosts entries for SSH client
  knownHosts = [
    phoneKnownHost
  ];
}
