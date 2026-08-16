# SSH public keys for authorized_keys: who may reach chise.
# Where chise reaches out to is the other direction and lives in
# private-configuration/machines/chise/ssh.nix, sourced by the ssh router
# at machine-configuration/network/ssh/ssh-private-home-manager.nix.
let
  phoneKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android";
  rinKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICpNZt8hGVbToPSE0nqVFXsGSM3Zae2tAH/lmVN5rD1x rin";
  kiraKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJw+IAmg/Vwv7U3BKyKl5fE+VidKx3ZPp8fkWJTy4jNG kira";
in
{
  authorizedKeys = [
    phoneKey
    rinKey
    kiraKey
  ];
}
