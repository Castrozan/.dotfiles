# SSH public keys for authorized_keys
# Known hosts with private IPs are now generated at runtime
# by the activation script in home/ssh.nix (reads from /run/agenix/ssh-hosts)
let
  phoneKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android";
  workPcKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/";
in
{
  authorizedKeys = [
    phoneKey
    workPcKey
  ];
}
