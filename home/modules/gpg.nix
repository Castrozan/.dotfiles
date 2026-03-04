{
  pkgs,
  config,
  ...
}:
let
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  importGpgPrivateKeyFromAgenix = pkgs.writeShellScript "import-gpg-private-key-from-agenix" ''
    set -euo pipefail

    GPG_PRIVATE_KEY_FILE="${secretsDirectory}/gpg-private-key"

    if [ ! -f "$GPG_PRIVATE_KEY_FILE" ]; then
      echo "GPG private key not found at $GPG_PRIVATE_KEY_FILE, skipping import" >&2
      exit 0
    fi

    EXISTING_KEY_COUNT=$(${pkgs.gnupg}/bin/gpg --list-secret-keys 2>/dev/null | grep -c "^sec" || true)

    if [ "$EXISTING_KEY_COUNT" -gt 0 ]; then
      exit 0
    fi

    ${pkgs.gnupg}/bin/gpg --batch --import "$GPG_PRIVATE_KEY_FILE" 2>/dev/null

    KEY_FINGERPRINT=$(${pkgs.gnupg}/bin/gpg --list-secret-keys --with-colons 2>/dev/null \
      | grep "^fpr" \
      | head -1 \
      | cut -d: -f10)

    if [ -n "$KEY_FINGERPRINT" ]; then
      echo "$KEY_FINGERPRINT:6:" | ${pkgs.gnupg}/bin/gpg --import-ownertrust 2>/dev/null
    fi
  '';
in
{
  programs.gpg = {
    enable = true;
    settings = {
      keyid-format = "long";
    };
  };

  services.gpg-agent = {
    enable = true;
    pinentry.package = pkgs.pinentry-curses;
  };

  home.activation.importGpgPrivateKeyFromAgenix =
    config.lib.dag.entryAfter
      [
        "writeBoundary"
        "agenix"
      ]
      ''
        run ${importGpgPrivateKeyFromAgenix}
      '';
}
