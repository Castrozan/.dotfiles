{
  security.pki.caCertificateBlacklist =
    (import ./distrusted-certificate-authorities.nix).nixCertificateBundle;
}
