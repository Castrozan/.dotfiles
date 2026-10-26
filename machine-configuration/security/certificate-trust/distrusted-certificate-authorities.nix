let
  nixCertificateBundle = [ "emSign ECC Root CA - G3" ];
in
{
  inherit nixCertificateBundle;
  appleCertificateBundle = nixCertificateBundle ++ [ "AAA Certificate Services" ];
}
