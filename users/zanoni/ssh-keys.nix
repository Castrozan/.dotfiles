# SSH public keys for authorized_keys
# This file centralizes SSH key management for better maintainability
let
  # Phone SSH public key
  phoneKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android";
in
{
  # List of all authorized SSH public keys
  authorizedKeys = [
    phoneKey
  ];
}
