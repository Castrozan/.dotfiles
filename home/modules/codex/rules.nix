{ pkgs, ... }:
let
  inherit (pkgs) bash;
in
{
  home.activation.codexRules = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
            set -euo pipefail

            CODEX_RULES_DIR="$HOME/.codex/rules"
            RULES_FILE="$CODEX_RULES_DIR/default.rules"
            mkdir -p "$CODEX_RULES_DIR"
            touch "$RULES_FILE"

            # Ensure key allow-rules exist without deleting Codex-added ones.
            ${bash}/bin/bash -eu -o pipefail <<'SH'
      rules_file="$HOME/.codex/rules/default.rules"

      want_lines=(
        'prefix_rule(pattern=["docker", "run"], decision="allow")'
        'prefix_rule(pattern=["docker", "compose", "up"], decision="allow")'
        'prefix_rule(pattern=["glab", "mr", "view"], decision="allow")'
        'prefix_rule(pattern=["glab", "mr", "note"], decision="allow")'
        'prefix_rule(pattern=["rm", "-f", "docs/redis-local-testing.md", "devenv.nix"], decision="allow")'
        'prefix_rule(pattern=["bin/rebuild"], decision="allow")'
        'prefix_rule(pattern=["./bin/rebuild"], decision="allow")'
      )

      tmp="$(mktemp)"
      cp "$rules_file" "$tmp"

      for line in "''${want_lines[@]}"; do
        if ! grep -Fqx "$line" "$tmp"; then
          printf '%s\n' "$line" >> "$tmp"
        fi
      done

      mv "$tmp" "$rules_file"
      SH
    '';
  };
}
