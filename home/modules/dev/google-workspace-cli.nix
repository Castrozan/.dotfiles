{ pkgs, inputs, ... }:
let
  googleWorkspaceCliPackage =
    inputs.google-workspace-cli.packages.${pkgs.stdenv.hostPlatform.system}.default;

  chromeGlobalUrlOpener = pkgs.writeShellScriptBin "google-workspace-cli-open-url-in-chrome-global" ''
    set -Eeuo pipefail

    readonly authentication_url="''${1:-}"

    main() {
      if [ -z "$authentication_url" ]; then
        echo "usage: google-workspace-cli-open-url-in-chrome-global <url>" >&2
        exit 1
      fi

      exec google-chrome-stable \
        --user-data-dir="$HOME/.config/chrome-global" \
        --class=chrome-global \
        --enable-features=UseNativeNotifications \
        "$authentication_url"
    }

    main "$@"
  '';

  googleWorkspaceCliAuthSetupWithChromeGlobal = pkgs.writeShellScriptBin "google-workspace-cli-auth-setup-with-chrome-global" ''
    set -Eeuo pipefail

    readonly google_workspace_cli_binary="${googleWorkspaceCliPackage}/bin/gws"
    readonly chrome_global_url_opener_binary="${chromeGlobalUrlOpener}/bin/google-workspace-cli-open-url-in-chrome-global"

    main() {
      export PATH="${pkgs.google-cloud-sdk}/bin:''${PATH:+:$PATH}"
      export BROWSER="$chrome_global_url_opener_binary"
      exec "$google_workspace_cli_binary" auth setup "$@"
    }

    main "$@"
  '';

  googleWorkspaceCliAuthLoginWithChromeGlobal = pkgs.writeShellScriptBin "google-workspace-cli-auth-login-with-chrome-global" ''
    set -Eeuo pipefail

    readonly google_workspace_cli_binary="${googleWorkspaceCliPackage}/bin/gws"
    readonly chrome_global_url_opener_binary="${chromeGlobalUrlOpener}/bin/google-workspace-cli-open-url-in-chrome-global"

    _open_authentication_url_when_available() {
      local authentication_output_path="$1"
      local authentication_url=""

      while true; do
        authentication_url=$(grep -Eom1 'https://[^[:space:]]+' "$authentication_output_path" || true)

        if [ -n "$authentication_url" ]; then
          "$chrome_global_url_opener_binary" "$authentication_url" >/dev/null 2>&1 &
          return 0
        fi

        sleep 1
      done
    }

    main() {
      local authentication_output_path=""
      local authentication_url_watcher_process_id=""
      local google_workspace_cli_exit_status=""

      authentication_output_path=$(mktemp)
      trap 'rm -f "$authentication_output_path"' EXIT

      _open_authentication_url_when_available "$authentication_output_path" &
      authentication_url_watcher_process_id="$!"

      set +e
      "$google_workspace_cli_binary" auth login "$@" 2>&1 | tee "$authentication_output_path"
      google_workspace_cli_exit_status="''${PIPESTATUS[0]}"
      set -e

      if kill -0 "$authentication_url_watcher_process_id" 2>/dev/null; then
        kill "$authentication_url_watcher_process_id" 2>/dev/null || true
      fi

      wait "$authentication_url_watcher_process_id" 2>/dev/null || true

      return "$google_workspace_cli_exit_status"
    }

    main "$@"
  '';
in
{
  home.packages = [
    googleWorkspaceCliPackage
    pkgs.google-cloud-sdk
    chromeGlobalUrlOpener
    googleWorkspaceCliAuthSetupWithChromeGlobal
    googleWorkspaceCliAuthLoginWithChromeGlobal
  ];
}
