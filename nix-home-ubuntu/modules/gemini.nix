{ pkgs, latest, ... }:
{
  home.packages = with pkgs; [
    (writeShellScriptBin "gemini" ''
      # Create a temporary passwd file with current user info
      TEMP_PASSWD=$(mktemp)
      echo "$(id -un):x:$(id -u):$(id -g):$(id -un):$HOME:/bin/bash" > "$TEMP_PASSWD"

      # Use bubblewrap to create a proper user context with /etc/passwd
      exec ${bubblewrap}/bin/bwrap \
        --dev-bind / / \
        --bind "$TEMP_PASSWD" /etc/passwd \
        --unshare-user \
        --uid $(id -u) \
        --gid $(id -g) \
        ${latest.gemini-cli}/bin/gemini "$@"

      # Cleanup
      rm -f "$TEMP_PASSWD"
    '')
  ];
}
