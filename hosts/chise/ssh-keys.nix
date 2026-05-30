# SSH public keys for authorized_keys
# Known hosts with private IPs are now generated at runtime
# by the activation script in home/ssh.nix (reads from /run/agenix/ssh-hosts)
let
  phoneKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android";
  jojoKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/ jojo";
  rinKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGyaFnjj9zi0BO5w6+CSjkO6L3A1nGveR651ZDHz9pa+ rin";
  kiraKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJw+IAmg/Vwv7U3BKyKl5fE+VidKx3ZPp8fkWJTy4jNG kira";
in
{
  authorizedKeys = [
    phoneKey
    jojoKey
    rinKey
    kiraKey
  ];
}
