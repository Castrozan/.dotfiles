{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  distrustedCertificateAuthorities = import ../distrusted-certificate-authorities.nix;

  distrustModuleBlacklist =
    (import ../certificate-authority-distrust-system.nix).security.pki.caCertificateBlacklist;

  distrustedBundle = pkgs.cacert.override {
    blacklist = distrustedCertificateAuthorities.nixCertificateBundle;
  };

  appleBundleActivation =
    (import ../apple-certificate-bundle-distrust-nix-darwin.nix {
      inherit lib pkgs;
    }).system.activationScripts.postActivation.text.content;
in
{
  domain-security-certificate-trust-system-bundle-drops-emsign-ecc-root-g3 =
    pkgs.runCommand "check-domain-security-certificate-trust-system-bundle-drops-emsign-ecc-root-g3"
      { nativeBuildInputs = [ pkgs.openssl ]; }
      ''
        bundle=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
        filtered=${distrustedBundle}/etc/ssl/certs/ca-bundle.crt
        extract_root() {
          awk -v name="$1" '$0 == name { found = 1 } found && /BEGIN CERTIFICATE/ { printing = 1 } printing { print } printing && /END CERTIFICATE/ { exit }' "$bundle"
        }
        extract_root "emSign ECC Root CA - G3" > emsign-root.pem
        extract_root "ISRG Root X1" > isrg-root.pem
        openssl verify -CAfile "$bundle" emsign-root.pem || {
          echo "the unfiltered nixpkgs bundle no longer trusts emSign ECC Root CA - G3; the distrust list entry may be stale or misspelled" >&2
          exit 1
        }
        if openssl verify -CAfile "$filtered" emsign-root.pem; then
          echo "the distrust list must remove emSign ECC Root CA - G3, whose eight weak-key intermediates let anyone forge a trusted certificate for any host" >&2
          exit 1
        fi
        openssl verify -CAfile "$filtered" isrg-root.pem || {
          echo "the distrust list must leave unrelated roots trusted" >&2
          exit 1
        }
        touch $out
      '';

  domain-security-certificate-trust-system-module-blacklists-every-distrusted-authority =
    mkEvalCheck "domain-security-certificate-trust-system-module-blacklists-every-distrusted-authority"
      (distrustModuleBlacklist == distrustedCertificateAuthorities.nixCertificateBundle)
      "the shared system module must feed the whole distrust list to security.pki.caCertificateBlacklist so NixOS and nix-darwin hosts build the same filtered Nix bundle that curl, git, Python, Node and Go read";

  domain-security-certificate-trust-apple-bundle-filter-covers-every-distrusted-authority =
    mkEvalCheck
      "domain-security-certificate-trust-apple-bundle-filter-covers-every-distrusted-authority"
      (
        lib.hasInfix "--bundle-path /etc/ssl/cert.pem" appleBundleActivation
        && lib.all (
          commonName:
          lib.hasInfix "--distrusted-common-name ${lib.escapeShellArg commonName}" appleBundleActivation
        ) distrustedCertificateAuthorities.appleCertificateBundle
      )
      "darwin activation must strip every distrusted authority from Apple's /etc/ssl/cert.pem, which /usr/bin/curl and /usr/bin/python3 read through LibreSSL and which Apple has not updated, so the AAA Certificate Services cross-signs keep vouching for the compromised eMudhra intermediates there";
}
