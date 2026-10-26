{ lib, pkgs, ... }:
let
  distrustedCommonNameArguments = lib.concatMapStringsSep " " (
    commonName: "--distrusted-common-name ${lib.escapeShellArg commonName}"
  ) (import ./distrusted-certificate-authorities.nix).appleCertificateBundle;
in
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    ${pkgs.python3}/bin/python3 -I ${./scripts/remove_distrusted_certificates_from_bundle.py} \
      --bundle-path /etc/ssl/cert.pem ${distrustedCommonNameArguments}
  '';
}
