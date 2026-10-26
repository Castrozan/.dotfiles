let
  systemCertificateBundle = "/etc/ssl/certs/ca-certificates.crt";
  defaultEnvironment = "NIX_SSL_CERT_FILE=${systemCertificateBundle}";
in
{
  environment.variables.NIX_SSL_CERT_FILE = systemCertificateBundle;
  systemd.settings.Manager.DefaultEnvironment = defaultEnvironment;
  systemd.user.extraConfig = ''
    DefaultEnvironment="${defaultEnvironment}"
  '';
}
