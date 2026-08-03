{
  pkgs,
  lib,
  hostname,
  config,
  ...
}:
let
  hostsWithClaudeGo = [
    "chise"
    "kira"
    "rin"
  ];
  claudeGoEnabledOnThisHost = lib.elem hostname hostsWithClaudeGo;

  opencodeGoBaseUrl = "https://opencode.ai/zen/go";
  opencodeGoModel = "qwen3.7-plus";

  claudeGoLauncher = pkgs.writeShellScriptBin "claude-go" ''
    opencodeGoApiKeyFile="$HOME/.secrets/opencode-api-key"
    if [ ! -f "$opencodeGoApiKeyFile" ] || [ ! -r "$opencodeGoApiKeyFile" ]; then
      echo "claude-go: no readable API key at $opencodeGoApiKeyFile" >&2
      echo "deploy the opencode-api-key agenix secret and retry" >&2
      exit 1
    fi
    unset ANTHROPIC_AUTH_TOKEN
    export ANTHROPIC_API_KEY="$(cat "$opencodeGoApiKeyFile")"
    export ANTHROPIC_BASE_URL="${opencodeGoBaseUrl}"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="${opencodeGoModel}"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="${opencodeGoModel}"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="${opencodeGoModel}"
    exec ${config.claude.package}/bin/claude --model "${opencodeGoModel}" "$@"
  '';
in
{
  config = lib.mkIf claudeGoEnabledOnThisHost {
    home.packages = [ claudeGoLauncher ];
  };
}
